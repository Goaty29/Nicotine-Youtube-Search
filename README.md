# YouTube Search plugin for Nicotine+

> **Unofficial.** This plugin is not made or endorsed by the Nicotine+ developers. It was made with the help of [Claude](https://claude.ai), an AI assistant by Anthropic.

Adds YouTube, Bandcamp, Discogs and Spotify searches to the right-click menu of files when you browse a user's shares. It guesses the artist and title from the file name and opens the search in your browser.

Tested with Nicotine+ 3.3.7 and 3.3.11.

![The Search on YouTube item in the right-click menu](menu-screenshot.png)

## Install on Windows

1. Download `youtube_search-release.zip` from the [latest release](../../releases/latest) and unzip it.
2. Close Nicotine+.
3. Press Win+R, type `%AppData%\nicotine`, and press Enter.
4. If there is no `plugins` folder there, create one.
5. Copy the whole `youtube_search` folder into `plugins`, so you have `%AppData%\nicotine\plugins\youtube_search\__init__.py`.
6. Start Nicotine+. Go to Preferences, then Plugins, tick **YouTube Search**, and click Apply.
7. Close and reopen any browse tabs that were already open. The new menu items only appear in tabs opened after the plugin is enabled.

Tip: Preferences > Plugins > **Add Plugins** opens the plugins folder for you.

## Install on Linux and macOS

Same steps, but the plugins folder is `~/.local/share/nicotine/plugins` on Linux and `~/Library/Application Support/nicotine/plugins` on macOS. Flatpak users: `~/.var/app/org.nicotine_plus.Nicotine/data/nicotine/plugins`.

## Use

Right-click one or more files in a browse tab and pick one of these:

| Menu item | What it opens |
|---|---|
| **Open first YouTube video** | The first video from the YouTube results, skipping ads. If it can't find one (no internet, YouTube changed its page), it opens the results page instead. |
| **Search on YouTube** | The YouTube results page. |
| **Search on Bandcamp** | Bandcamp search results. |
| **Search on Discogs** | Discogs search results. |
| **Search on Spotify** | Spotify search in the web player. |

Each selected file opens its own tab, up to 5 at a time. You can also type `/yt <file name or text>` in a chat box. It opens the first video, or the results page if **Open first YouTube video** is turned off.

## Settings

Go to Preferences, then Plugins, select **YouTube Search**, and click Settings.

- Tick or untick each menu item to choose which ones show up in the right-click menu. All of them are on by default. Changes apply to browse tabs you open afterwards, so close and reopen a tab to see them.
- **YouTube search URL** changes where the YouTube items search, for example `https://music.youtube.com/search?q=%s` for YouTube Music.

## How the name is cleaned up

| File name | Search |
|---|---|
| `01 - Daft Punk - One More Time [320].mp3` | Daft Punk One More Time |
| `2025-07-23 - No Chasa - Shall We Do It Again [ADC024].mp3` | No Chasa Shall We Do It Again |
| `03-the_pro-teens-spray_it_dont_say_it-uvu.mp3` | the pro teens spray it dont say it |
| `Portishead - Glory Box (Official Video).webm` | Portishead Glory Box |
| `Radiohead\OK Computer\03 Subterranean Homesick Alien.flac` | Radiohead Subterranean Homesick Alien |

It removes the extension, track numbers, dates, anything in [square brackets], and noise in (parentheses) like bitrates, years and "Official Video". It turns underscores into spaces and splits on " - ". If the file name has no artist, it takes one from the folder names.

## Caveat

Nicotine+ has no official way for plugins to add file menu items, so this plugin hooks into the browse tab's internal code. A future Nicotine+ release could break it. If that happens, the `/yt` command will still work.

## License

GPL-3.0-or-later, the same license as Nicotine+. See [LICENSE](LICENSE).
