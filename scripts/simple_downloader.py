#!/usr/bin/env python3
"""
Script SIMPLE et RAPIDE pour télécharger des playlists YouTube Music
Version simplifiée mais optimisée
"""

import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import os
import time
from pathlib import Path

def download_video(video_info, output_dir):
    """Télécharge une vidéo"""
    video_id = video_info.get('id')
    title = video_info.get('title', 'Unknown').replace('/', '_').replace('\\', '_')
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Options yt-dlp optimisées
    ydl_opts = {
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': os.path.join(output_dir, f'{title}.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ {title[:50]}...")
        return True
    except:
        print(f"❌ {title[:50]}...")
        return False

def download_playlist_simple(playlist_url, threads=6):
    """Télécharge une playlist simplement"""
    print(f"📋 Extraction de la playlist...")
    
    # Extraire les infos de la playlist
    ydl_opts = {'quiet': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    playlist_title = info.get('title', 'Playlist').replace('/', '_').replace('\\', '_')
    entries = [e for e in info.get('entries', []) if e and e.get('id')]
    
    if not entries:
        print("❌ Aucune vidéo trouvée")
        return
    
    print(f"🎵 {playlist_title} - {len(entries)} titres")
    
    # Créer le dossier
    Path(playlist_title).mkdir(exist_ok=True)
    
    # Téléchargement parallèle
    print(f"🚀 Téléchargement avec {threads} threads...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(lambda v: download_video(v, playlist_title), entries))
    
    # Statistiques
    success = sum(results)
    elapsed = time.time() - start_time
    print(f"\n🎉 Terminé: {success}/{len(entries)} réussis en {elapsed:.1f}s")

def main():
    """Fonction principale simple"""
    print("🎵 === TÉLÉCHARGEUR YOUTUBE MUSIC SIMPLE === 🎵\n")
    
    url = input("🔗 URL de la playlist: ").strip()
    if not url:
        print("❌ URL requise")
        return
    
    try:
        threads = int(input("⚙️  Nombre de threads (défaut 6): ") or "6")
        threads = max(1, min(threads, 12))
    except:
        threads = 6
    
    print()
    download_playlist_simple(url, threads)

if __name__ == "__main__":
    main()