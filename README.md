# YouTube Music Downloader

J'en avais marre d'attendre des heures pour télécharger mes playlists, alors j'ai fait ce script.

## Ce que ça fait

- Télécharge plusieurs playlists en même temps
- Utilise du multithreading pour aller plus vite
- Sort en MP3 320kbps 
- Reprend automatiquement si ça plante

## Résultats

Playlist de 100 titres : ~5 minutes au lieu de 20
Playlist de 400 titres : ~15 minutes au lieu de 2h

## Installation

```bash
git clone https://github.com/Felzow47/youtube-music-downloader.git
cd youtube-music-downloader
pip install yt-dlp
```

Il faut aussi FFmpeg installé sur votre machine.

## Utilisation

Le plus simple sur Windows : double-cliquez sur `ULTRA_DOWNLOADER.bat`

Sinon : `python scripts/ultra_downloader.py`

## Les scripts

**ultra_downloader.py** - Pour plusieurs grosses playlists en parallèle  
**multi_threaded_downloader.py** - Version équilibrée  
**simple_downloader.py** - Version basique pour tester  

## Config recommandée

- 2-3 playlists max en parallèle 
- 6-8 threads par playlist
- Ne pas abuser sinon YouTube vous limite

## Légal

Respectez les droits d'auteur et les conditions d'utilisation de YouTube.