#!/usr/bin/env python3
"""
Script de téléchargement YouTube Music multithreadé optimisé
Utilise yt-dlp avec concurrent.futures pour des performances maximales
"""

import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import logging
import time
import threading
from pathlib import Path
import sys

# Configuration du logging
logger = logging.getLogger("yt_dlp_multithread")
logger.setLevel(logging.INFO)

# Handler pour fichier d'erreurs
file_handler = logging.FileHandler("download_errors.log", encoding="utf-8")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Handler pour console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(console_handler)

# Verrous pour éviter les conflits d'affichage
print_lock = threading.Lock()
stats_lock = threading.Lock()

# Statistiques globales
class DownloadStats:
    def __init__(self):
        self.total_videos = 0
        self.completed = 0
        self.failed = 0
        self.start_time = None
        
    def increment_completed(self):
        with stats_lock:
            self.completed += 1
            
    def increment_failed(self):
        with stats_lock:
            self.failed += 1
            
    def get_progress(self):
        with stats_lock:
            return self.completed, self.failed, self.total_videos

stats = DownloadStats()

def safe_print(message):
    """Impression thread-safe"""
    with print_lock:
        print(message)

def progress_hook(d):
    """Hook de progression pour yt-dlp"""
    if d['status'] == 'downloading':
        filename = os.path.basename(d.get('filename', 'Unknown'))
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A')
        
        # Affichage simplifié pour éviter le spam
        if percent.endswith('0%') or percent.endswith('5%'):
            safe_print(f"📥 {filename[:50]}... | {percent} | {speed}")
    
    elif d['status'] == 'finished':
        filename = os.path.basename(d.get('filename', 'Unknown'))
        safe_print(f"✅ Terminé: {filename[:50]}...")

def get_optimal_ydl_opts(output_dir):
    """Configuration optimisée pour yt-dlp"""
    return {
        # Format audio de la meilleure qualité
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
        
        # Extraction et conversion audio
        'writethumbnail': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        
        # Post-processing pour MP3 haute qualité
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',  # Qualité maximale
        }, {
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        }],
        
        # Template de sortie
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        
        # Options de performance
        'concurrent_fragment_downloads': 4,  # Téléchargements de fragments parallèles
        'fragment_retries': 3,
        'retries': 3,
        'file_access_retries': 3,
        
        # Gestion des erreurs
        'ignoreerrors': True,
        'no_warnings': False,
        'extract_flat': False,
        
        # Hook de progression
        'progress_hooks': [progress_hook],
        
        # Options réseau
        'socket_timeout': 30,
        'http_chunk_size': 10485760,  # 10MB chunks
        
        # Éviter les limitations YouTube
        'sleep_interval': 0,
        'max_sleep_interval': 2,
        'sleep_interval_subtitles': 0,
    }

def download_single_video(video_info, output_dir, thread_id):
    """Télécharge une seule vidéo"""
    video_id = video_info.get('id')
    title = video_info.get('title', 'Unknown')
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    safe_print(f"🚀 [Thread-{thread_id}] Démarrage: {title[:50]}...")
    
    ydl_opts = get_optimal_ydl_opts(output_dir)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        stats.increment_completed()
        safe_print(f"✅ [Thread-{thread_id}] Succès: {title[:50]}...")
        return True
        
    except Exception as e:
        stats.increment_failed()
        error_msg = f"❌ [Thread-{thread_id}] Échec: {title[:50]}... | Erreur: {str(e)}"
        safe_print(error_msg)
        logger.error(f"Erreur pour {title} ({url}): {str(e)}")
        return False

def extract_playlist_info(playlist_url):
    """Extrait les informations d'une playlist"""
    safe_print(f"📋 Extraction des informations de la playlist...")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            
        playlist_title = info.get('title', 'Playlist_Unknown')
        entries = info.get('entries', [])
        
        # Filtrer les entrées valides
        valid_entries = [entry for entry in entries if entry and entry.get('id')]
        
        safe_print(f"📊 Playlist trouvée: {playlist_title}")
        safe_print(f"📊 Nombre de titres: {len(valid_entries)}")
        
        return playlist_title, valid_entries
        
    except Exception as e:
        logger.error(f"Erreur extraction playlist {playlist_url}: {str(e)}")
        safe_print(f"❌ Erreur extraction playlist: {str(e)}")
        return None, []

def download_playlist_multithreaded(playlist_url, max_workers=8):
    """Télécharge une playlist en multithreadé"""
    safe_print(f"\n🎵 Traitement de la playlist: {playlist_url}")
    
    # Extraction des informations
    playlist_title, entries = extract_playlist_info(playlist_url)
    if not entries:
        safe_print("❌ Aucune vidéo trouvée dans la playlist")
        return
    
    # Création du dossier de sortie
    output_dir = playlist_title.replace('/', '_').replace('\\', '_')
    Path(output_dir).mkdir(exist_ok=True)
    
    # Mise à jour des statistiques
    stats.total_videos = len(entries)
    stats.completed = 0
    stats.failed = 0
    stats.start_time = time.time()
    
    safe_print(f"🎯 Démarrage du téléchargement parallèle avec {max_workers} threads")
    safe_print(f"📁 Dossier de sortie: {output_dir}")
    
    # Téléchargement parallèle
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre tous les téléchargements
        future_to_video = {}
        for i, video_info in enumerate(entries):
            future = executor.submit(download_single_video, video_info, output_dir, i % max_workers)
            future_to_video[future] = video_info
        
        # Traiter les résultats au fur et à mesure
        for future in as_completed(future_to_video):
            video_info = future_to_video[future]
            try:
                result = future.result()
                
                # Affichage du progrès
                completed, failed, total = stats.get_progress()
                progress_percent = ((completed + failed) / total) * 100
                safe_print(f"📈 Progrès: {completed}/{total} réussis, {failed} échecs ({progress_percent:.1f}%)")
                
            except Exception as e:
                title = video_info.get('title', 'Unknown')
                logger.error(f"Exception future pour {title}: {str(e)}")
    
    # Statistiques finales
    elapsed_time = time.time() - stats.start_time
    completed, failed, total = stats.get_progress()
    
    safe_print(f"\n📊 === RÉSULTATS FINAUX ===")
    safe_print(f"✅ Téléchargements réussis: {completed}")
    safe_print(f"❌ Téléchargements échoués: {failed}")
    safe_print(f"📊 Total: {total}")
    safe_print(f"⏱️  Temps écoulé: {elapsed_time:.1f}s")
    safe_print(f"🚀 Vitesse moyenne: {completed/elapsed_time:.2f} téléchargements/seconde")

def download_multiple_playlists(playlist_urls, max_workers_per_playlist=6):
    """Télécharge plusieurs playlists de manière séquentielle avec multithreading par playlist"""
    total_playlists = len(playlist_urls)
    
    safe_print(f"🎵 Démarrage du téléchargement de {total_playlists} playlists")
    safe_print(f"⚙️  Configuration: {max_workers_per_playlist} threads par playlist")
    
    for i, playlist_url in enumerate(playlist_urls, 1):
        safe_print(f"\n{'='*60}")
        safe_print(f"📋 Playlist {i}/{total_playlists}")
        safe_print(f"{'='*60}")
        
        download_playlist_multithreaded(playlist_url, max_workers_per_playlist)
        
        if i < total_playlists:
            safe_print("⏸️  Pause de 2 secondes avant la playlist suivante...")
            time.sleep(2)

def main():
    """Fonction principale"""
    print("🎵 === TÉLÉCHARGEUR YOUTUBE MUSIC MULTITHREADÉ === 🎵")
    print()
    print("💡 Conseils:")
    print("   - Utilisez 4-8 threads pour un bon équilibre performance/stabilité")
    print("   - Le script télécharge en MP3 320kbps (meilleure qualité)")
    print("   - Les erreurs sont loggées dans 'download_errors.log'")
    print()
    
    # Saisie des URLs
    print("📝 Collez vos URLs de playlists YouTube Music, séparées par des virgules:")
    raw_input = input("🔗 URLs: ").strip()
    
    if not raw_input:
        print("❌ Aucune URL fournie. Arrêt du programme.")
        return
    
    # Parse des URLs
    playlist_urls = [url.strip() for url in raw_input.split(',') if url.strip()]
    
    if not playlist_urls:
        print("❌ Aucune URL valide trouvée. Arrêt du programme.")
        return
    
    # Configuration du nombre de threads
    try:
        max_workers = int(input(f"⚙️  Nombre de threads par playlist (recommandé: 6): ") or "6")
        max_workers = max(1, min(max_workers, 12))  # Limiter entre 1 et 12
    except ValueError:
        max_workers = 6
    
    print(f"\n🚀 Configuration finale: {len(playlist_urls)} playlists, {max_workers} threads par playlist")
    input("⏯️  Appuyez sur Entrée pour commencer...")
    
    # Démarrage des téléchargements
    start_time = time.time()
    
    try:
        download_multiple_playlists(playlist_urls, max_workers)
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt demandé par l'utilisateur")
        return
    except Exception as e:
        print(f"\n❌ Erreur critique: {str(e)}")
        logger.error(f"Erreur critique: {str(e)}")
        return
    
    # Temps total
    total_time = time.time() - start_time
    print(f"\n🎉 === TERMINÉ ===")
    print(f"⏱️  Temps total: {total_time:.1f}s")
    print("📁 Vérifiez vos dossiers pour les fichiers téléchargés!")

if __name__ == "__main__":
    main()