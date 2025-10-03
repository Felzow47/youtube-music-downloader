# 🎵 Downloads Folder

All your downloaded YouTube Music playlists will appear here, organized by folder.

## Automatic structure

- Each playlist = a separate folder
- MP3 files 320kbps with metadata
- Folder names automatically cleaned
- Duplicate handling with suffixes (_1, _2, etc.)

## Example structure

```
downloads/
├── My Rock Playlist/
│   ├── Song 1.mp3
│   ├── Song 2.mp3
│   └── Song 3.mp3
├── My Pop Favorites/
│   ├── Hit 1.mp3
│   └── Hit 2.mp3
└── Chill Vibes/
    ├── Relaxing Track 1.mp3
    └── Ambient Sound.mp3
```

## Notes

- Special characters in playlist names are automatically cleaned for filesystem compatibility
- If a playlist already exists, duplicate songs are skipped
- All files include proper metadata (title, artist, album when available)
- Files are saved in high quality MP3 format (320kbps)