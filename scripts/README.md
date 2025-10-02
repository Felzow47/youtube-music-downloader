# 📁 Scripts Python - Téléchargeurs YouTube Music

Ce dossier contient les scripts Python optimisés pour télécharger des playlists YouTube Music.

## 🎯 Scripts disponibles

### 1. `ultra_downloader.py` ⚡ **RECOMMANDÉ**
**Le plus performant**
- Télécharge **plusieurs playlists simultanément**
- Multithreading par playlist (6-8 threads recommandés)
- Capacité théorique : 20+ téléchargements simultanés
- Statistiques en temps réel
- **Usage** : Pour les gros volumes (plusieurs playlists, 100+ titres)

### 2. `multi_threaded_downloader.py` 🎯 **Équilibré**
**Bon compromis performance/simplicité**
- Une playlist à la fois mais multithreadée
- Interface utilisateur claire avec progression
- Logging détaillé des erreurs
- **Usage** : Pour un usage standard (1-2 playlists à la fois)

### 3. `simple_downloader.py` 🚀 **Simple**
**Version minimaliste**
- Interface ultra-simple
- Code compact et lisible
- Multithreading basique mais efficace
- **Usage** : Pour des tests ou utilisations ponctuelles

## 🚀 Lancement recommandé

**Utilisez les fichiers .bat à la racine** :
- `ULTRA_DOWNLOADER.bat` → Lance `ultra_downloader.py`
- `MULTI_DOWNLOADER.bat` → Lance `multi_threaded_downloader.py`  
- `SIMPLE_DOWNLOADER.bat` → Lance `simple_downloader.py`

## ⚙️ Lancement manuel

Si vous préférez utiliser Python directement :

```bash
# Depuis la racine du projet
python scripts/ultra_downloader.py
python scripts/multi_threaded_downloader.py
python scripts/simple_downloader.py
```

## 🔧 Configuration optimale

### Pour playlists 400+ titres :
- **Script** : `ultra_downloader.py`
- **Playlists simultanées** : 2-3 max
- **Threads par playlist** : 6-8

### Pour playlists 50-200 titres :
- **Script** : `multi_threaded_downloader.py`
- **Threads** : 6-8

### Pour tests/usage ponctuel :
- **Script** : `simple_downloader.py`
- **Threads** : 4-6

## 📊 Comparaison des performances

| Script | Playlists // | Threads/playlist | Vitesse relative | Complexité |
|--------|-------------|------------------|------------------|------------|
| Simple | 1 | 6 | 1x | Faible |
| Multi | 1 | 8 | 1.5x | Moyenne |
| Ultra | 2-3 | 6-8 | **3-5x** | Élevée |

---

💡 **Conseil** : Commencez par `ultra_downloader.py` pour vos gros téléchargements !