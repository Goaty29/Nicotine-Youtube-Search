# Changelog

All notable changes to this plugin are listed here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the plugin uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.2.0] - 2026-11-04

### Added

- **Search on Bandcamp**, **Search on Discogs** and **Search on Spotify** in the
  right-click menu.
- **Search on YouTube** is back as its own menu item that always opens the results
  page, next to **Open first YouTube video**.
- A setting for each menu item to show or hide it. All are on by default.

### Changed

- Better artist and title guessing from file names: disc-track numbers (`1-03`,
  `Track 05`), track numbers in the middle (`Artist - Album - 05 - Title`), quality
  tags at the end (`320kbps`, `FLAC`, `24bit`), `feat.`/`ft.`/`featuring` credits are
  dropped, names that start with a number (`50 Cent`, `2 Unlimited`) are kept, and the
  artist is taken from folder names while skipping `CD1`, `Music` and `Various Artists`.
- The "open the first video" setting is replaced by the **Open first YouTube video**
  menu toggle. If you had turned it off, untick that menu item instead.

## [1.1.0] - 2026-11-03

First public release on GitHub.

### Added

- **Open the first video directly**: picking Search on YouTube now opens the first
  video from the results straight away, skipping ads, playlists, channels and Shorts.
  If no video can be found (no internet, or YouTube changed its page), the normal
  search results open instead.
- A plugin setting to turn this off and always get the results page.
- Install guide for Windows, Linux, macOS and Flatpak, and a screenshot of the menu.
- GPL-3.0-or-later license, the same as Nicotine+.

## [1.0.0]

Not published on GitHub.

### Added

- **Search on YouTube** item in the right-click menu of files in browse tabs. Each
  selected file opens its own tab, up to 5 at a time.
- Artist and title guessing from the file name: removes the extension, track numbers,
  dates, [square brackets] and noise in (parentheses), turns underscores into spaces,
  and takes the artist from the folder names when the file name has none.
- `/yt <text>` chat command.
- A setting for the search URL, for example to use YouTube Music.

[Unreleased]: https://github.com/Goaty29/nicotine-youtube-search/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/Goaty29/nicotine-youtube-search/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Goaty29/nicotine-youtube-search/releases/tag/v1.1.0
