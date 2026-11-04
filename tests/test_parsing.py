"""Tests for the file name parsing. Run with: python -m pytest tests  (or python tests/test_parsing.py)"""
import os
import sys
import types

# The plugin imports Nicotine+ modules at the top; stub them so the parser can be tested alone.
for name in ("pynicotine", "pynicotine.events", "pynicotine.pluginsystem", "pynicotine.utils"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["pynicotine.events"].events = None
sys.modules["pynicotine.pluginsystem"].BasePlugin = object
sys.modules["pynicotine.utils"].open_uri = None
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from youtube_search import guess_query, parse_artist_title  # noqa: E402

CASES = [
    # (path, artist, title)
    # The README examples
    (r"Music\Daft Punk\01 - Daft Punk - One More Time [320].mp3", "Daft Punk", "One More Time"),
    ("2025-07-23 - No Chasa - Shall We Do It Again [ADC024].mp3", "No Chasa", "Shall We Do It Again"),
    ("03-the_pro-teens-spray_it_dont_say_it-uvu.mp3", "", "the pro teens spray it dont say it"),
    ("Portishead - Glory Box (Official Video).webm", "Portishead", "Glory Box"),
    (r"Radiohead\OK Computer\03 Subterranean Homesick Alien.flac", "Radiohead", "Subterranean Homesick Alien"),
    # Track numbers
    ("01. Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    ("01) Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    ("1-03 Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    ("A2 - Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    ("Track 05 - Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    ("01-Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - 05 - Around the World.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Homework - 05 - Around the World.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - 1997 - Homework - 05 - Around the World.mp3", "Daft Punk", "Around the World"),
    # Numbers that belong to the name
    ("50 Cent - In Da Club.mp3", "50 Cent", "In Da Club"),
    ("2 Unlimited - Get Ready for This.mp3", "2 Unlimited", "Get Ready for This"),
    ("Smashing Pumpkins - 1979.mp3", "Smashing Pumpkins", "1979"),
    (r"Ariana Grande\thank u, next\7 rings.mp3", "Ariana Grande", "7 rings"),
    ("U2 - One.mp3", "U2", "One"),
    # Years, bitrate and format tags
    ("Daft Punk - Around the World (1997).mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World [1997] [FLAC 24-96].flac", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World 320kbps.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World (320 kbps).mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World (24bit 96kHz).flac", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World {WEB}.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World (Remastered 2021).mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World (HQ Audio).mp3", "Daft Punk", "Around the World"),
    # feat. credits
    ("Calvin Harris feat. Rihanna - This Is What You Came For.mp3", "Calvin Harris", "This Is What You Came For"),
    ("Calvin Harris ft. Rihanna - This Is What You Came For.mp3", "Calvin Harris", "This Is What You Came For"),
    ("Calvin Harris - This Is What You Came For (feat. Rihanna).mp3", "Calvin Harris", "This Is What You Came For"),
    ("Calvin Harris - This Is What You Came For [ft. Rihanna].mp3", "Calvin Harris", "This Is What You Came For"),
    ("Calvin Harris featuring Rihanna - This Is What You Came For.mp3", "Calvin Harris", "This Is What You Came For"),
    ("Simon & Garfunkel - The Boxer.mp3", "Simon & Garfunkel", "The Boxer"),
    ("Calvin Harris - This Is What You Came For feat. Rihanna (Radio Edit).mp3", "Calvin Harris",
     "This Is What You Came For (Radio Edit)"),
    ("Daft Punk - Around the World (320).mp3", "Daft Punk", "Around the World"),
    # Remixes and versions are kept, they matter for the search
    ("Daft Punk - One More Time (Radio Edit).mp3", "Daft Punk", "One More Time (Radio Edit)"),
    ("Daft Punk - One More Time - Radio Edit.mp3", "Daft Punk", "One More Time Radio Edit"),
    ("Artist - Charlotte's Web.mp3", "Artist", "Charlotte's Web"),
    ("Pink Floyd\\The Wall\\CD2\\2-04 Comfortably Numb.flac", "Pink Floyd", "Comfortably Numb"),
    ("Daft Punk - Around the World V0.mp3", "Daft Punk", "Around the World"),
    # Separators and underscores
    ("Daft_Punk_-_Around_the_World.mp3", "Daft Punk", "Around the World"),
    ("01_daft_punk_-_around_the_world.mp3", "daft punk", "around the world"),
    ("Daft Punk – Around the World.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk -Around the World.mp3", "Daft Punk", "Around the World"),
    ("Jay-Z - 99 Problems.mp3", "Jay-Z", "99 Problems"),
    # Artist from the folders
    (r"@@share\Music\Daft Punk - Homework (1997) [FLAC]\05 Around the World.flac", "Daft Punk", "Around the World"),
    (r"Music\Daft Punk\Homework\CD1\05 Around the World.flac", "Daft Punk", "Around the World"),
    (r"Music\Daft Punk\1997 - Homework\05 - Around the World.flac", "Daft Punk", "Around the World"),
    (r"Music\Daft Punk - 1997 - Homework\05. Around the World.flac", "Daft Punk", "Around the World"),
    (r"Music\Various Artists\Summer Hits\05 Around the World.mp3", "", "Around the World"),
    (r"Music\VA - Summer Hits\05 Around the World.mp3", "", "Around the World"),
    ("Music/Daft Punk/Homework/05 - Around the World.mp3", "Daft Punk", "Around the World"),
    # File name already has the artist: don't take another one from the folders
    (r"Music\VA - Summer Hits\05 - Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    # Website addresses added by download sites
    ("Junglewood - Passistas (Original Mix) www.electronicfresh.com.mp3", "Junglewood", "Passistas (Original Mix)"),
    ("Benan - Just Be (Original Mix)  www.electronicfresh.com.mp3", "Benan", "Just Be (Original Mix)"),
    ("Gustaff, Franklyn Watts - Burning (Original Mix)  www.electronicfresh.com.mp3", "Gustaff, Franklyn Watts",
     "Burning (Original Mix)"),
    ("Daft Punk - Around the World heydj.pro.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World - www.mp3-site.net.mp3", "Daft Punk", "Around the World"),
    ("Daft Punk - Around the World (www.Site.ORG).mp3", "Daft Punk", "Around the World"),
    ("www.zippymp3.ru - Daft Punk - Around the World.mp3", "Daft Punk", "Around the World"),
    (r"Music\Daft Punk - Homework www.site.com\05 Around the World.mp3", "Daft Punk", "Around the World"),
    ("Junglewood - Passistas (Original Mix).mp3", "Junglewood", "Passistas (Original Mix)"),
    # Dots that are not websites
    ("will.i.am - Scream & Shout.mp3", "will.i.am", "Scream & Shout"),
    ("Mr. Nunez - DAMN! (Original Mix).mp3", "Mr. Nunez", "DAMN! (Original Mix)"),
    ("Dr. Dre - Still D.R.E.mp3", "Dr. Dre", "Still D.R.E"),
    # Plain text from the /yt command
    ("daft punk around the world", "", "daft punk around the world"),
]


def test_cases():
    failures = []
    for path, artist, title in CASES:
        got = parse_artist_title(path)
        if got != (artist, title):
            failures.append(f"{path!r}\n    got      {got}\n    expected {(artist, title)}")
    assert not failures, "\n" + "\n".join(failures)


def test_guess_query_joins_artist_and_title():
    assert guess_query(r"Music\Daft Punk\01 - Daft Punk - One More Time [320].mp3") == "Daft Punk One More Time"
    assert guess_query("") == ""


if __name__ == "__main__":
    test_cases()
    test_guess_query_joins_artist_and_title()
    print(f"{len(CASES)} cases OK")
