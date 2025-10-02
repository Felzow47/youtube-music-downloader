#!/usr/bin/env python3
"""
Script de téléchargement YouTube Music ULTRA-OPTIMISÉ
Téléchargement simultané de plusieurs playlists avec multithreading par playlist
"""

import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import logging
import time
import threading
from pathlib import Path
import sys
from queue import Queue
import json

# Créer le dossier logs s'il n'existe pas
Path("logs").mkdir(exist_ok=True)

# Configuration du logging
logger = logging.getLogger("yt_dlp_ultra")
logger.setLevel(logging.INFO)

# Handler pour fichier d'erreurs
file_handler = logging.FileHandler("logs/ultra_download_errors.log", encoding="utf-8")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Handler pour console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(console_handler)

# Verrous pour éviter les conflits
print_lock = threading.Lock()
stats_lock = threading.Lock()

class GlobalStats:
    """Statistiques globales thread-safe"""
    def __init__(self):
        self.playlists_total = 0
        self.playlists_completed = 0
        self.videos_total = 0
        self.videos_completed = 0
        self.videos_failed = 0
        self.start_time = None
        
    def add_playlist(self, video_count):
        with stats_lock:
            self.playlists_total += 1
            self.videos_total += video_count
    
    def complete_playlist(self):
        with stats_lock:
            self.playlists_completed += 1
    
    def add_video_success(self):
        with stats_lock:
            self.videos_completed += 1
    
    def add_video_failure(self):
        with stats_lock:
            self.videos_failed += 1
    
    def get_stats(self):
        with stats_lock:
            return (self.playlists_completed, self.playlists_total, 
                   self.videos_completed, self.videos_failed, self.videos_total)

global_stats = GlobalStats()

def safe_print(message):
    """Impression thread-safe avec horodatage"""
    with print_lock:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

def progress_hook(d):
    """Hook de progression minimaliste pour éviter le spam"""
    if d['status'] == 'finished':
        filename = os.path.basename(d.get('filename', 'Unknown'))
        safe_print(f"✅ Fini: {filename[:40]}...")

def get_ultra_ydl_opts(output_dir):
    """Configuration ultra-optimisée pour yt-dlp"""
    return {
        # Format audio optimal
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        
        # Post-processing pour MP3 320kbps
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }, {
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        }],
        
        # Template de sortie avec sanitization
        'outtmpl': os.path.join(output_dir, '%(title).100s.%(ext)s'),
        
        # Options de performance maximales
        'concurrent_fragment_downloads': 8,  # Plus de fragments parallèles
        'fragment_retries': 5,
        'retries': 5,
        'file_access_retries': 5,
        'retry_sleep_functions': {'http': lambda n: min(4 * (2 ** n), 30)},
        
        # Optimisations réseau
        'socket_timeout': 60,
        'http_chunk_size': 16777216,  # 16MB chunks
        'buffersize': 16384,
        
        # Gestion des erreurs
        'ignoreerrors': True,
        'no_warnings': True,
        'extract_flat': False,
        
        # Hook de progression
        'progress_hooks': [progress_hook],
        
        # Éviter les limitations
        'sleep_interval': 0,
        'max_sleep_interval': 1,
        'sleep_interval_requests': 0,
        'sleep_interval_subtitles': 0,
        
        # Options de sécurité
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writethumbnail': False,
        'writeinfojson': False,
    }

def download_single_video(video_info, output_dir, playlist_name):
    """Télécharge une seule vidéo avec gestion d'erreur optimisée"""
    video_id = video_info.get('id')
    title = video_info.get('title', 'Unknown')[:50]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Vérifier si le fichier existe déjà
    potential_files = list(Path(output_dir).glob(f"{title}*.mp3"))
    if potential_files:
        global_stats.add_video_success()
        return True
    
    ydl_opts = get_ultra_ydl_opts(output_dir)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        global_stats.add_video_success()
        return True
        
    except Exception as e:
        global_stats.add_video_failure()
        logger.error(f"[{playlist_name}] Erreur pour {title}: {str(e)}")
        return False

def extract_playlist_info_fast(playlist_url):
    """Extraction rapide des informations de playlist"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': False,
        'socket_timeout': 30,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
        
        playlist_title = info.get('title', f'Playlist_{int(time.time())}')
        # Nettoyer le nom du dossier
        playlist_title = "".join(c for c in playlist_title if c.isalnum() or c in (' ', '-', '_')).strip()
        
        entries = [entry for entry in info.get('entries', []) if entry and entry.get('id')]
        
        return playlist_title, entries
        
    except Exception as e:
        logger.error(f"Erreur extraction playlist {playlist_url}: {str(e)}")
        return None, []

def download_playlist_ultra_fast(playlist_url, video_threads=8):
    """Télécharge une playlist avec multithreading optimisé"""
    playlist_name, entries = extract_playlist_info_fast(playlist_url)
    
    if not entries:
        safe_print(f"❌ Aucune vidéo trouvée: {playlist_url}")
        return False
    
    # Création du dossier avec gestion des conflits
    output_dir = playlist_name
    counter = 1
    while Path(output_dir).exists() and any(Path(output_dir).iterdir()):
        output_dir = f"{playlist_name}_{counter}"
        counter += 1
    
    Path(output_dir).mkdir(exist_ok=True)
    
    global_stats.add_playlist(len(entries))
    safe_print(f"🎵 [{playlist_name}] Démarrage: {len(entries)} titres, {video_threads} threads")
    
    success_count = 0
    
    # Téléchargement parallèle des vidéos
    with ThreadPoolExecutor(max_workers=video_threads) as executor:
        futures = []
        for video_info in entries:
            future = executor.submit(download_single_video, video_info, output_dir, playlist_name)
            futures.append(future)
        
        # Collecter les résultats
        for future in as_completed(futures):
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                logger.error(f"[{playlist_name}] Exception dans future: {str(e)}")
    
    global_stats.complete_playlist()
    safe_print(f"✅ [{playlist_name}] Terminé: {success_count}/{len(entries)} réussis")
    return True

def download_all_playlists_parallel(playlist_urls, playlist_threads=3, video_threads_per_playlist=6):
    """Télécharge toutes les playlists en parallèle"""
    safe_print(f"🚀 DÉMARRAGE ULTRA-OPTIMISÉ")
    safe_print(f"📊 {len(playlist_urls)} playlists, {playlist_threads} playlists simultanées")
    safe_print(f"⚙️  {video_threads_per_playlist} threads vidéo par playlist")
    
    global_stats.start_time = time.time()
    
    # Téléchargement parallèle des playlists
    with ThreadPoolExecutor(max_workers=playlist_threads) as executor:
        futures = []
        for i, playlist_url in enumerate(playlist_urls):
            future = executor.submit(download_playlist_ultra_fast, playlist_url, video_threads_per_playlist)
            futures.append((future, playlist_url, i+1))
        
        # Traiter les résultats
        for future, playlist_url, playlist_num in futures:
            try:
                result = future.result()
                if result:
                    safe_print(f"🎉 Playlist {playlist_num}/{len(playlist_urls)} terminée avec succès")
                else:
                    safe_print(f"❌ Playlist {playlist_num}/{len(playlist_urls)} échouée")
            except Exception as e:
                safe_print(f"❌ Erreur critique playlist {playlist_num}: {str(e)}")
                logger.error(f"Erreur critique playlist {playlist_url}: {str(e)}")

def print_final_stats():
    """Affiche les statistiques finales"""
    playlists_done, playlists_total, videos_done, videos_failed, videos_total = global_stats.get_stats()
    elapsed = time.time() - global_stats.start_time
    
    safe_print(f"\n{'='*60}")
    safe_print(f"🎉 === STATISTIQUES FINALES ===")
    safe_print(f"{'='*60}")
    safe_print(f"📋 Playlists: {playlists_done}/{playlists_total} terminées")
    safe_print(f"🎵 Vidéos: {videos_done}/{videos_total} réussies")
    safe_print(f"❌ Échecs: {videos_failed}")
    safe_print(f"⏱️  Temps total: {elapsed:.1f}s")
    safe_print(f"🚀 Vitesse: {videos_done/elapsed:.2f} vidéos/seconde")
    safe_print(f"💪 Efficacité: {(videos_done/videos_total)*100:.1f}%")
    safe_print(f"{'='*60}")

def main():
    """Fonction principale ultra-optimisée"""
    print("🎵 === TÉLÉCHARGEUR YOUTUBE MUSIC ULTRA-OPTIMISÉ === 🎵")
    print()
    print("⚡ PERFORMANCES MAXIMALES:")
    print("   - Playlists téléchargées en parallèle")
    print("   - Multithreading par playlist")
    print("   - MP3 320kbps avec métadonnées")
    print("   - Gestion intelligente des doublons")
    print("   - Logging complet des erreurs")
    print()
    
    # Saisie des URLs
    print("📝 Collez vos URLs de playlists YouTube Music (séparées par des virgules):")
    raw_input = input("🔗 URLs: ").strip()
    
    if not raw_input:
        print("❌ Aucune URL fournie.")
        return
    
    playlist_urls = [url.strip() for url in raw_input.split(',') if url.strip()]
    
    if not playlist_urls:
        print("❌ Aucune URL valide.")
        return
    
    print(f"\n📊 {len(playlist_urls)} playlists détectées")
    
    # Configuration avancée
    try:
        playlist_threads = int(input("🔀 Playlists simultanées (recommandé 2-3): ") or "2")
        playlist_threads = max(1, min(playlist_threads, 4))
    except ValueError:
        playlist_threads = 2
    
    try:
        video_threads = int(input("⚙️  Threads vidéo par playlist (recommandé 6-8): ") or "6")
        video_threads = max(1, min(video_threads, 12))
    except ValueError:
        video_threads = 6
    
    print(f"\n🎯 Configuration finale:")
    print(f"   - {len(playlist_urls)} playlists")
    print(f"   - {playlist_threads} playlists simultanées")
    print(f"   - {video_threads} threads vidéo par playlist")
    print(f"   - Capacité théorique: {playlist_threads * video_threads} téléchargements simultanés")
    
    input("⏯️  Appuyez sur Entrée pour lancer l'ultra-téléchargement...")
    
    try:
        download_all_playlists_parallel(playlist_urls, playlist_threads, video_threads)
        print_final_stats()
        
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt demandé par l'utilisateur")
        print_final_stats()
    except Exception as e:
        print(f"\n❌ Erreur critique: {str(e)}")
        logger.error(f"Erreur critique main: {str(e)}")
        print_final_stats()

if __name__ == "__main__":
    main()