# YouTube Music Downloader

J'en avais marre ## Comment utiliser

Le plus simple : double-cliquez sur `ULTRA_DOWNLOADER.bat`

Ou sinon : `python scripts/ultra_downloader.py`

Pour les réglages, je recommande :
- 2-3 playlists max en parallèle (sinon YouTube risque de vous limiter)
- 6-8 threads par playliste des heures pour télécharger mes playlists, alors j'ai fait ce script qui utilise plusieurs threads pour aller beaucoup plus vite.

Avec mes anciennes méthodes, une playlist de 400 titres me prenait facile 2-3h. Maintenant c'est fait en 20-30 minutes.

## Ce que ça fait

- Télécharge plusieurs playlists en même temps
- Utilise plusieurs threads par playlist 
- Sort en MP3 320kbps avec les métadonnées
- Reprend automatiquement en cas d'erreur
- Interface simple avec des .bat pour Windows

## 📁 Organisation des fichiers

```
📁 yt/
├── 🚀 ULTRA_DOWNLOADER.bat     - Lance le script ultra-optimisé
├── 🎯 MULTI_DOWNLOADER.bat     - Lance le script équilibré  
├── 🚀 SIMPLE_DOWNLOADER.bat    - Lance le script simple
├── 📖 README.md                - Ce fichier
├── 📁 scripts/                 - Scripts Python optimisés
│   ├── ultra_downloader.py     - Script ultra-optimisé
│   ├── multi_threaded_downloader.py - Script équilibré
│   └── simple_downloader.py    - Script simple
└── 📁 .venv/                   - Environnement Python
```

## Les scripts

J'ai fait 3 versions selon les besoins :

**ultra_downloader.py** - Pour quand vous avez plusieurs grosses playlists
- Télécharge 2-3 playlists en parallèle
- 6-8 threads par playlist
- Le plus rapide mais demande une bonne connexion

**multi_threaded_downloader.py** - Un bon compromis
- Une playlist à la fois mais avec du multithreading
- Interface claire avec progression
- Bon pour un usage normal

**simple_downloader.py** - Version basique
- Simple et direct
- Pour tester ou usage ponctuel

## 🚀 Utilisation rapide

### Pour la plupart des cas (recommandé):
- Double-cliquez sur `ULTRA_DOWNLOADER.bat`
- Ou lancez : `python scripts\ultra_downloader.py`

### Configuration recommandée:
- **Playlists simultanées**: 2-3 (évite les limitations YouTube)
- **Threads par playlist**: 6-8 (optimal pour la plupart des connexions)

## Résultats concrets

Playlist de 100 titres : ~5 minutes au lieu de 20
Playlist de 400 titres : ~15 minutes au lieu de 2h

Le tout en MP3 320kbps avec les métadonnées.

## � Installation rapide

### 1. Cloner le repository
```bash
git clone https://github.com/Felzow47/youtube-music-downloader.git
cd youtube-music-downloader
```

### 2. Installer les dépendances
```bash
pip install yt-dlp
```

### 3. Installer FFmpeg
- **Windows**: Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 4. Lancer le téléchargeur
```bash
# Windows
ULTRA_DOWNLOADER.bat

# Ou manuellement
python scripts/ultra_downloader.py
```

## 🔧 Prérequis

- Python 3.7+
- yt-dlp
- FFmpeg (pour la conversion MP3)

## 📝 Utilisation détaillée

### Ultra Downloader (recommandé):
1. Double-cliquez sur `ULTRA_DOWNLOADER.bat`
2. Collez vos URLs de playlists (séparées par des virgules)
3. Configurez le nombre de threads
4. Laissez le script travailler!

### Format des URLs supportées:
- `https://music.youtube.com/playlist?list=...`
- `https://www.youtube.com/playlist?list=...`
- Playlists publiques et non-listées

## 📁 Structure des fichiers téléchargés

```
📁 Nom_de_la_Playlist/
├── 🎵 Titre_1.mp3
├── 🎵 Titre_2.mp3
└── 🎵 ...
```

## 📋 Logging

Les erreurs sont automatiquement sauvées dans:
- `ultra_download_errors.log` (Ultra downloader)
- `download_errors.log` (Multi threaded)

## ⚠️ Notes importantes

1. **Respect des limites**: Ne dépassez pas 3 playlists simultanées pour éviter les limitations YouTube
2. **Connexion**: Une connexion stable est recommandée
3. **Espace disque**: Vérifiez l'espace disponible (une playlist de 400 titres ≈ 3-4 GB)
4. **Légalité**: Respectez les droits d'auteur et les conditions d'utilisation de YouTube

## 🎵 Comparaison des performances

| Script | Playlists simultanées | Threads/playlist | Vitesse | Utilisation |
|--------|----------------------|------------------|---------|-------------|
| Simple | 1 | 6 | Rapide | Usage basique |
| Multi  | 1 | 8 | Très rapide | Usage standard |
| Ultra  | 2-3 | 6-8 | **Ultra rapide** | **Usage intensif** |

## 🚀 Conseils d'optimisation

### Pour les grandes playlists (400+ titres):
- Utilisez `ultra_downloader.py`
- 2 playlists simultanées max
- 8 threads par playlist

### Pour les petites playlists (<100 titres):
- Utilisez `simple_downloader.py`
- 6-8 threads suffisent

### Pour un usage quotidien:
- Utilisez `multi_threaded_downloader.py`
- Configuration par défaut

---

**Bon téléchargement! 🎵✨**