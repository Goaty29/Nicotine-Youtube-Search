# YouTube Search plugin for Nicotine+ (tested with 3.3.7 and 3.3.11).
import re
import sys
import threading
import urllib.request
import urllib.parse

from pynicotine.events import events
from pynicotine.pluginsystem import BasePlugin
from pynicotine.utils import open_uri

AUDIO_EXTS = {"mp3", "flac", "ogg", "opus", "m4a", "aac", "wav", "wma", "alac", "ape", "aiff",
              "mp4", "mkv", "webm"}
# Any [...] or {...} block: bitrates, catalog numbers like [ADC024], uploader tags
SQUARE = re.compile(r"\[[^\]]*\]|\{[^}]*\}")
# (...) blocks that only add noise to a YouTube search
PAREN_JUNK = re.compile(
    r"\([^)]*(?:\d{3}|kbps|flac|mp3|web|vinyl|rip|remaster(?:ed)?|bonus|explicit|"
    r"official|video|audio|lyrics?|visuali[sz]er|hq|hd)[^)]*\)",
    re.IGNORECASE)
DATE = re.compile(r"^\d{4}(?:[-.]\d{2}(?:[-.]\d{2})?)?$")             # 2025, 2025-07, 2025-07-23
TRACK = re.compile(r"^(?:[A-D]?\d{1,3}(?:[-.]\d{1,3})?|cd\d+)$", re.I)  # 03, 1-03, A2, cd1


def clean(text):
    text = re.sub(r"\s+", " ", text.replace("_", " "))
    return text.strip(" -\u2013.")


def strip_junk(text):
    return PAREN_JUNK.sub("", SQUARE.sub("", text))


def is_noise(field):
    return bool(DATE.match(field) or TRACK.match(field))


def guess_query(file_path):
    """'Music\\Daft Punk\\01 - Daft Punk - One More Time [320].mp3' -> 'Daft Punk One More Time'"""
    parts = [p for p in re.split(r"[\\/]", file_path) if p]
    name = parts[-1] if parts else file_path
    stem, dot, ext = name.rpartition(".")
    if dot and ext.lower() in AUDIO_EXTS:
        name = stem
    name = strip_junk(name).strip()

    if " " not in name and "-" in name:
        # Scene style: 03-the_pro-teens-spray_it_dont_say_it-uvu
        # Fields are split by "-", spaces are "_", last field is the release group.
        fields = [f for f in name.split("-") if f]
        while fields and is_noise(fields[0]):
            fields.pop(0)
        if len(fields) >= 3:
            fields.pop()  # release group tag
        return clean(" ".join(fields))

    # Normal style: "01 - Artist - Title", "2025-07-23 - Artist - Title", "01. Title"
    name = clean(name)
    name = re.sub(r"^(?:[A-D]?\d{1,3}(?:[-.]\d{1,3})?)(?:\s*[-.)]\s*|\s+)(?=\D)", "", name)
    fields = [clean(f) for f in re.split(r"\s+[-\u2013]\s+|\s*_-_\s*", name)]
    fields = [f for f in fields if f and not is_noise(f)]

    if len(fields) >= 2:
        return clean(f"{fields[-2]} {fields[-1]}")

    title = fields[0] if fields else name
    # No artist in the file name: take it from the folders ("Artist - Album (Year)" or "Artist/Album")
    artist = ""
    for folder in reversed(parts[:-1]):
        if " - " in folder:
            artist = clean(strip_junk(folder).split(" - ")[0])
            break
    if not artist and len(parts) >= 3:
        artist = clean(strip_junk(parts[-3]))
    return clean(f"{artist} {title}")


YOUTUBE_RESULTS = "https://www.youtube.com/results?search_query=%s&hl=en"
FIRST_VIDEO = re.compile(r'"videoRenderer":\{"videoId":"([\w-]{11})"')
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    # Skip the EU cookie consent page, which has no results on it
    "Cookie": "SOCS=CAI; CONSENT=YES+1",
}


def find_first_video(html):
    """Return the id of the first real video in a YouTube results page (skips ads,
    playlists, channels and Shorts shelves), or None."""
    match = FIRST_VIDEO.search(html)
    return match.group(1) if match else None


def fetch_first_video(query, timeout=8, results_url=YOUTUBE_RESULTS):
    request = urllib.request.Request(results_url % urllib.parse.quote_plus(query), headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", "replace")
    return find_first_video(html)


class Plugin(BasePlugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = {
            "open_first_result": True,
            "url_template": "https://www.youtube.com/results?search_query=%s",
        }
        self.metasettings = {
            "open_first_result": {
                "description": "Open the first video directly instead of the search results "
                               "(falls back to the results page if it can't find one)",
                "type": "bool"},
            "url_template": {
                "description": "Search URL (%s = query). e.g. https://music.youtube.com/search?q=%s",
                "type": "string"}
        }
        self.commands = {
            "yt": {
                "callback": self.yt_command,
                "description": "Search YouTube for a file name or text",
                "parameters": ["<text>"],
            }
        }
        self._original_init = None

    def search_url(self, query):
        return self.settings["url_template"].replace("%s", urllib.parse.quote_plus(query))

    def open_search(self, file_path):
        query = guess_query(file_path)
        if not query:
            return

        if not self.settings["open_first_result"]:
            self.log("YouTube search: %s", query)
            open_uri(self.search_url(query))
            return

        # Fetch the results page in the background so the window doesn't freeze
        threading.Thread(target=self._open_first_result, args=(query,), daemon=True).start()

    def _open_first_result(self, query):
        try:
            video_id = fetch_first_video(query)
            note = ""
        except Exception as error:  # network error, timeout, blocked...
            video_id = None
            note = f" (lookup failed: {error})"

        if video_id:
            message = f"YouTube: opening first result for {query}"
            url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            message = f"YouTube search: {query}{note or ' (no video found)'}"
            url = self.search_url(query)

        # GUI work and logging belong on the main thread
        events.invoke_main_thread(self._open_url, url, message)

    def _open_url(self, url, message):
        self.log(message)
        open_uri(url)

    def yt_command(self, args, **_unused):
        if args.strip():
            self.open_search(args)

    # GUI hook. Nicotine+ has no plugin API for file menus, so we wrap the
    # UserBrowse tab constructor and append our own item. Applies to browse
    # tabs opened after the plugin is enabled.
    def loaded_notification(self):
        if "pynicotine.gtkgui" not in sys.modules:
            return  # running headless, no menus to add to

        from pynicotine.gtkgui import userbrowse

        plugin = self
        original_init = userbrowse.UserBrowse.__init__

        def patched_init(browse, *args, **kwargs):
            original_init(browse, *args, **kwargs)

            def on_youtube(*_args):
                folder = browse.get_selected_folder_path()
                for basename in list(browse.selected_files)[:5]:
                    plugin.open_search(f"{folder}{basename}")

            browse.file_popup_menu.add_items(
                ("", None),
                ("#" + "Search on _YouTube", on_youtube),
            )

        self._original_init = original_init
        userbrowse.UserBrowse.__init__ = patched_init
        self.log("Right-click a file in a browse tab and choose 'Search on YouTube'. "
                 "Close and reopen browse tabs that were already open.")

    def disable(self):
        if self._original_init:
            from pynicotine.gtkgui import userbrowse
            userbrowse.UserBrowse.__init__ = self._original_init
            self._original_init = None
