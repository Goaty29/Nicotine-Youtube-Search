# Changelog

All notable changes to this plugin are listed here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the plugin uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/Goaty29/nicotine-youtube-search/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Goaty29/nicotine-youtube-search/releases/tag/v1.1.0
