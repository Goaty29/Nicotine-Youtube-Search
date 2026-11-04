# YouTube Search plugin for Nicotine+ (tested with 3.3.7 and 3.3.11).
import re
import sys
import threading
import urllib.request
import urllib.parse

from pynicotine.events import events
from pynicotine.pluginsystem import BasePlugin
from pynicotine.utils import open_uri

# ---------------------------------------------------------------------------
# File name parsing: guess the artist and title from a shared file's path.
# Soulseek only gives us the path (no ID3 tags), so everything comes from the
# file and folder names.
# ---------------------------------------------------------------------------

AUDIO_EXTS = {"mp3", "flac", "ogg", "opus", "m4a", "aac", "wav", "wma", "alac", "ape", "aiff",
              "aif", "wv", "dsf", "mp4", "mkv", "webm"}
# Any [...] or {...} block: bitrates, catalog numbers like [ADC024], uploader tags
SQUARE = re.compile(r"\[[^\]]*\]|\{[^}]*\}")
# (...) blocks that only add noise to a YouTube search
PAREN_JUNK = re.compile(
    r"\([^)]*(?:\b\d{4}\b|\b(?:320|256|192|128|v0|v2)\b|\d+\s?kbps|\d+\s?k?hz|\d+\s?bit|flac|mp3|\bweb\b|vinyl|\brip\b|"
    r"remaster(?:ed)?|bonus|explicit|official|\bvideo\b|\baudio\b|lyrics?|visuali[sz]er|"
    r"\bhq\b|\bhd\b|\b4k\b)[^)]*\)",
    re.IGNORECASE)
# Format and quality tags left at the end of a name without brackets: "Title 320kbps FLAC"
TRAILING_TAGS = re.compile(
    r"(?:[\s._-]+(?:\d{2,3}\s?kbps|320|256|192|128|v[02]|flac|mp3|aac|alac|cbr|vbr|lossless|"
    r"\d{2}[\s-]?bit|\d{2,3}(?:[.,]\d)?\s?khz|(?:16|24)-(?:44|48|88|96|192)|webrip|cdrip))+$",
    re.IGNORECASE)
# Featured artist credits: "feat. X", "ft X", "featuring X", in or out of parentheses
FEAT = re.compile(r"\s*[(\[]?\s*\b(?:feat\.?|ft\.|ft\b|featuring)\s+[^()\[\]]*[)\]]?", re.IGNORECASE)
DATE = re.compile(r"^\d{4}(?:[-.]\d{2}(?:[-.]\d{2})?)?$")             # 2025, 2025-07, 2025-07-23
TRACK = re.compile(r"^(?:track\s*)?(?:[A-D]?\d{1,3}(?:[-.]\d{1,3})?|cd\s?\d+)$", re.I)  # 03, 1-03, A2, cd1
# A track number at the start of a name, with the separator after it
LEADING_TRACK = re.compile(r"^(?:track\s*)?([A-D]?\d{1,3}(?:[-.]\d{1,3})?)(\s*[-.)_]\s*|\s+)(?=\S)",
                           re.IGNORECASE)
FIELD_SPLIT = re.compile(r"\s+[-–—]\s+|\s*_-_\s*|\s+[-–—](?=\S)|(?<=\S)[-–—]\s+")
# Folder names that never hold the artist
DISC_FOLDER = re.compile(r"^(?:cd|dis[ck]|disc|side|vol(?:ume)?\.?)\s*[\dA-D]+$", re.IGNORECASE)
GENERIC_FOLDERS = {"music", "musik", "musique", "mp3", "mp3s", "flac", "audio", "albums", "singles",
                   "downloads", "download", "complete", "shared", "share", "soulseek", "nicotine",
                   "various artists", "various", "va", "compilations", "unknown artist", "misc"}
MIX_WORDS = re.compile(r"\b(?:mix|remix|edit|version|dub|vip|bootleg|rework|live|instrumental|"
                       r"acoustic|extended|radio)\b", re.IGNORECASE)


def clean(text):
    text = re.sub(r"\s+", " ", text.replace("_", " "))
    return text.strip(" -–—.,")


def strip_junk(text):
    text = PAREN_JUNK.sub("", SQUARE.sub("", text))
    return re.sub(r"\(\s*\)", "", text)


def strip_feat(text):
    """'Artist feat. Someone' -> 'Artist', 'Title (ft. Someone)' -> 'Title'"""
    return clean(FEAT.sub(" ", text))


def is_noise(field):
    return bool(DATE.match(field) or TRACK.match(field))


def strip_leading_track(name):
    """Remove '01 - ', '01. ', 'A2 ', '1-03 ' from the start of a name. A number followed by
    just a space is only removed when it's zero-padded or nothing else in the name looks like
    an artist, so '50 Cent - In Da Club' and '2 Unlimited - Get Ready' survive."""
    match = LEADING_TRACK.match(name)
    if not match:
        return name
    number, separator = match.groups()
    rest = name[match.end():]
    if separator.strip():
        # "01 - ", "01. ", "01) ". But "3.14 ..." is a number, not a track.
        return name if separator.strip() == "." and rest[:1].isdigit() else rest
    if number.startswith("0") or not number.isdigit():
        return rest  # "01 Title", "1-03 Title", "A2 Title"
    if FIELD_SPLIT.search(rest):
        return name  # "50 Cent - In Da Club"
    if len(number) == 1 and len(rest.split()) == 1:
        return name  # "7 rings"
    return rest  # "12 Title" with the artist in the folder name


def split_fields(name):
    return [clean(f) for f in FIELD_SPLIT.split(name) if clean(f)]


def artist_from_folders(folders):
    """Find the artist in folder names like 'Artist - Album (2019)', 'Artist/Album/CD1'
    or 'Artist/2019 - Album'. Looks at the three nearest real folders."""
    folders = [clean(strip_junk(f)) for f in folders]
    folders = [f for f in folders if f and not DISC_FOLDER.match(f)]
    nearest = list(reversed(folders))[:3]

    for folder in nearest:
        if folder.lower() in GENERIC_FOLDERS:
            continue
        fields = split_fields(folder)
        if len(fields) >= 2 and not is_noise(fields[0]):
            if fields[0].lower() in GENERIC_FOLDERS:
                continue  # "VA - Summer Hits"
            return strip_feat(fields[0])  # "Artist - Album" or "Artist - 2019 - Album"
        # "2019 - Album" or a plain album name: the artist is the folder above it

    # "Artist/Album/01 Title": the folder above the album
    if len(nearest) >= 2:
        candidate = nearest[1]
        if candidate.lower() not in GENERIC_FOLDERS and not is_noise(candidate):
            return strip_feat(candidate)
    return ""


def pick_artist_title(fields):
    """Choose artist and title from the ' - ' separated parts of a file name."""
    # "Artist - Album - 05 - Title": the track number marks where the title starts
    for index in range(1, len(fields) - 1):
        if TRACK.match(fields[index]) and not DATE.match(fields[index]):
            artist = next((f for f in fields[:index] if not is_noise(f)), "")
            title = " - ".join(f for f in fields[index + 1:] if not TRACK.match(f))
            return artist, title

    real = [f for f in fields if not is_noise(f)]
    if not real:
        return "", fields[-1] if fields else ""
    if len(real) == 1:
        # "Smashing Pumpkins - 1979": a number can be the title
        if fields[-1] != real[0]:
            return real[0], fields[-1]
        return "", real[0]
    if len(real) == 2:
        return real[0], real[1]

    # Three or more: "Artist - Title - Extended Mix" or "Artist - Album - Title"
    if MIX_WORDS.search(real[-1]) and len(real[-1].split()) <= 4:
        return real[0], f"{real[-2]} {real[-1]}"
    return real[0], real[-1]


def parse_scene(name):
    """'03-the_pro-teens-spray_it_dont_say_it-uvu': fields split by '-', spaces are '_',
    the last field is the release group."""
    fields = [f for f in name.split("-") if f]
    while fields and is_noise(fields[0]):
        fields.pop(0)
    if len(fields) >= 3:
        fields.pop()  # release group tag
    fields = [clean(f) for f in fields]
    if len(fields) == 2:
        return fields[0], fields[1]
    # Can't tell where a hyphenated artist ends, so keep it all as one search
    return "", clean(" ".join(fields))


def parse_artist_title(file_path):
    """Guess (artist, title) from a shared file's path. Either can be ''.

    'Music\\Daft Punk\\01 - Daft Punk - One More Time [320].mp3' -> ('Daft Punk', 'One More Time')
    """
    parts = [p for p in re.split(r"[\\/]", file_path.strip()) if p]
    if not parts:
        return "", ""
    name = parts[-1]
    stem, dot, ext = name.rpartition(".")
    if dot and ext.lower() in AUDIO_EXTS:
        name = stem
    name = strip_junk(name).strip()
    name = TRAILING_TAGS.sub("", name).strip()

    if " " not in name and "-" in name and "_-_" not in name:
        artist, title = parse_scene(name)
    else:
        name = strip_leading_track(clean(name))
        artist, title = pick_artist_title(split_fields(name))

    artist, title = strip_feat(artist), strip_feat(title)
    title = clean(TRAILING_TAGS.sub("", title))
    if not artist:
        artist = artist_from_folders(parts[:-1])
        # Don't repeat the artist when the title already starts with it
        if artist and title.lower().startswith(artist.lower()):
            artist = ""
    return artist, title


def guess_query(file_path):
    """'Music\\Daft Punk\\01 - Daft Punk - One More Time [320].mp3' -> 'Daft Punk One More Time'"""
    artist, title = parse_artist_title(file_path)
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


# Extra search sites. Each one has a setting that shows or hides its menu item.
# (setting key, menu label, setting description, search URL with %s for the query)
SEARCH_SITES = [
    ("menu_youtube_search", "Search on YouTube", "Show 'Search on YouTube' (results page)",
     None),  # uses the YouTube search URL setting
    ("menu_bandcamp", "Search on Bandcamp", "Show 'Search on Bandcamp'",
     "https://bandcamp.com/search?q=%s"),
    ("menu_discogs", "Search on Discogs", "Show 'Search on Discogs'",
     "https://www.discogs.com/search/?q=%s&type=all"),
    ("menu_spotify", "Search on Spotify", "Show 'Search on Spotify'",
     "https://open.spotify.com/search/%s"),
]


def build_url(template, query):
    # Query string templates ("?q=%s") use "+" for spaces. A path like Spotify's
    # "/search/%s" needs real %20 escapes, or the "+" signs end up in the search.
    if "?" in template.split("%s")[0]:
        quoted = urllib.parse.quote_plus(query)
    else:
        quoted = urllib.parse.quote(query, safe="")
    return template.replace("%s", quoted)


class Plugin(BasePlugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = {
            "menu_youtube_first": True,
            "menu_youtube_search": True,
            "menu_bandcamp": True,
            "menu_discogs": True,
            "menu_spotify": True,
            "url_template": "https://www.youtube.com/results?search_query=%s",
        }
        self.metasettings = {
            "menu_youtube_first": {
                "description": "Show 'Open first YouTube video' (opens the first video directly, "
                               "or the results page if it can't find one)",
                "type": "bool"},
        }
        for key, _label, description, _url in SEARCH_SITES:
            self.metasettings[key] = {"description": description, "type": "bool"}
        self.metasettings["url_template"] = {
            "description": "YouTube search URL (%s = query). "
                           "e.g. https://music.youtube.com/search?q=%s",
            "type": "string"}
        self.commands = {
            "yt": {
                "callback": self.yt_command,
                "description": "Search YouTube for a file name or text",
                "parameters": ["<text>"],
            }
        }
        self._original_init = None

    def search_url(self, query):
        return build_url(self.settings["url_template"], query)

    def menu_items(self):
        """(label, callback taking a file path) for each item turned on in the settings."""
        items = []
        if self.settings["menu_youtube_first"]:
            items.append(("Open first _YouTube video", self.open_first_video))
        for key, label, _description, url in SEARCH_SITES:
            if self.settings[key]:
                template = url or self.settings["url_template"]
                items.append((label, lambda path, t=template, name=label: self.open_site(path, t, name)))
        return items

    def open_site(self, file_path, template, name):
        query = guess_query(file_path)
        if query:
            self.log("%s: %s", (name, query))
            open_uri(build_url(template, query))

    def open_search(self, file_path):
        """YouTube results page, no auto-open."""
        self.open_site(file_path, self.settings["url_template"], "YouTube search")

    def open_first_video(self, file_path):
        query = guess_query(file_path)
        if not query:
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
        if not args.strip():
            return
        if self.settings["menu_youtube_first"]:
            self.open_first_video(args)
        else:
            self.open_search(args)

    # GUI hook. Nicotine+ has no plugin API for file menus, so we wrap the
    # UserBrowse tab constructor and append our own items. Applies to browse
    # tabs opened after the plugin is enabled (or after the settings change).
    def loaded_notification(self):
        if "pynicotine.gtkgui" not in sys.modules:
            return  # running headless, no menus to add to

        from pynicotine.gtkgui import userbrowse

        plugin = self
        original_init = userbrowse.UserBrowse.__init__

        def patched_init(browse, *args, **kwargs):
            original_init(browse, *args, **kwargs)

            items = plugin.menu_items()
            if not items:
                return

            def make_callback(open_file):
                def callback(*_args):
                    folder = browse.get_selected_folder_path()
                    for basename in list(browse.selected_files)[:5]:
                        open_file(f"{folder}{basename}")
                return callback

            browse.file_popup_menu.add_items(
                ("", None),
                *(("#" + label, make_callback(open_file)) for label, open_file in items),
            )

        self._original_init = original_init
        userbrowse.UserBrowse.__init__ = patched_init
        self.log("Right-click a file in a browse tab to search it on YouTube, Bandcamp, Discogs "
                 "or Spotify. Close and reopen browse tabs that were already open.")

    def disable(self):
        if self._original_init:
            from pynicotine.gtkgui import userbrowse
            userbrowse.UserBrowse.__init__ = self._original_init
            self._original_init = None
