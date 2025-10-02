# YouTube Music Downloader

[🇫🇷 Version française](README.md)

I was tired of waiting hours to download my playlists, so I made this script.

## What it does

- Downloads multiple playlists at the same time
- Uses multithreading to go faster
- Output in MP3 320kbps
- Automatically resumes if it crashes

## Results

100-song playlist: ~5 minutes instead of 20
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

## Recommended config

- 2-3 playlists max in parallel
- 6-8 threads per playlist
- Don't overdo it or YouTube will limit you

## Legal

Respect copyrights and YouTube's terms of service.