# YouTube Music Downloader

[🇫🇷 Version française](../README.md)

[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-Public-red.svg)]()
[![Status: Half-Abandoned](https://img.shields.io/badge/Status-Half--Abandoned-red.svg)]()

Scripts for download music on youtube music - Multithreading

> [!NOTE]
> ⚠️This project is probably abandoned.
> I no longer have the energy to maintain it due to ongoing issues with YouTube
> I recommend using : [youtube music playlist downloader from Blaze414](https://github.com/Blaze414/youtube-music-ultra-downloader)
---
I was tired of waiting hours to download my playlists, so I made this script.

## About

- Downloads multiple playlists at the same time
- Uses multithreading to go faster
- Output in MP3 320kbps
- Automatically resumes if it crashes

## Results

100-song playlist: ~5 minutes instead of 20 minutes 

400-song playlist: ~15 minutes instead of 2h

## Installation

```bash
git clone https://github.com/Felzow47/youtube-music-downloader.git
cd youtube-music-downloader
pip install yt-dlp
```

You also need FFmpeg installed on your machine.

## Usage

Easiest on Windows: double-click `ULTRA_DOWNLOADER.bat`

Otherwise: `python ultra_downloader.py`

## The script

**ultra_downloader.py** - Ultra-optimized script with all features:

- Multiple playlists downloaded in parallel
- Playlist verification before download
- Special characters handling in titles
- Enhanced user interface
- Detailed statistics
- Automatic organization in `downloads/` folder

## File organization

Downloaded playlists are automatically organized:

```text
yt/
├── downloads/
│   ├── My Rock Playlist/
│   │   ├── Song 1.mp3
│   │   └── Song 2.mp3
│   └── My Pop Playlist/
│       ├── Hit 1.mp3
│       └── Hit 2.mp3
└── ultra_downloader.py
```

## 🍪 YouTube Premium Access

If you have a YouTube Premium subscription and want to download Premium-exclusive songs:

1. Export your YouTube cookies using a browser extension
2. Place the `cookies.txt` file in the script folder
3. The script will automatically detect the cookies

👉 **Detailed guide**: Check [COOKIES_GUIDE_EN.md](COOKIES_GUIDE_EN.md) for complete instructions.

## Recommended config

- 2-3 playlists max in parallel
- 6-8 threads per playlist
- Don't overdo it or YouTube will limit you

## 🎉 Fork with graphical interface

A user has created a fork of this project and added a graphical interface as well as other features (and probably coded better than me XD)!

- Fork: [Blaze414/youtube-music-ultra-downloader](https://github.com/Blaze414/youtube-music-ultra-downloader)

Feel free to check out their version if you want a more visual experience!


## Legal

Respect copyrights and YouTube's terms of service.

---

