# YouTube Music Downloader

[🇬🇧 English version](docs/README_EN.md) | [📚 All documentation](docs/README.md)

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

Sinon : `python ultra_downloader.py`

## Le script

**ultra_downloader.py** - Script ultra-optimisé avec toutes les fonctionnalités :

- Téléchargement de plusieurs playlists en parallèle
- Vérification des playlists avant téléchargement
- Gestion des caractères spéciaux dans les titres
- Interface utilisateur améliorée
- Statistiques détaillées
- Organisation automatique dans le dossier `downloads/`

## Organisation des fichiers

Les playlists téléchargées sont automatiquement organisées :

```text
yt/
├── downloads/
│   ├── Ma Playlist Rock/
│   │   ├── Chanson 1.mp3
│   │   └── Chanson 2.mp3
│   └── Ma Playlist Pop/
│       ├── Hit 1.mp3
│       └── Hit 2.mp3
└── ultra_downloader.py
```

## 🍪 Accès YouTube Premium

Si vous avez un abonnement YouTube Premium et voulez télécharger des chansons exclusives Premium :

1. Exportez vos cookies YouTube avec une extension de navigateur
2. Placez le fichier `cookies.txt` dans le dossier du script
3. Le script détectera automatiquement les cookies

👉 **Guide détaillé** : Consultez [COOKIES_GUIDE.md](docs/COOKIES_GUIDE.md) pour les instructions complètes.

## Config recommandée

- 2-3 playlists max en parallèle
- 6-8 threads par playlist
- Ne pas abuser sinon YouTube vous limite

## Légal

Respectez les droits d'auteur et les conditions d'utilisation de YouTube.
