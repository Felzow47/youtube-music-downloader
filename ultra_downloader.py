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

# Logger pour yt-dlp (capture les erreurs internes)
yt_dlp_logger = logging.getLogger("yt-dlp")
yt_dlp_logger.addHandler(file_handler)

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

# Variables globales pour stocker les noms de fichiers créés
current_download_files = set()

def post_process_hook(d):
    """Hook pour capturer les noms de fichiers finaux créés"""
    if d.get('status') == 'finished':
        # Récupérer le chemin du fichier final
        filepath = d.get('filepath') or d.get('filename')
        if filepath and Path(filepath).suffix.lower() == '.mp3':
            current_download_files.add(str(Path(filepath)))

def clean_filename(title):
    """Nettoie un titre pour en faire un nom de fichier sûr"""
    if not title:
        return "Unknown"
    
    # Remplacer les astérisques par des X
    cleaned = title.replace('***', 'XXX').replace('**', 'XX').replace('*', 'X')
    
    # Remplacer d'autres caractères problématiques
    replacements = {
        '/': '-', '\\': '-', '|': '-', '<': '(', '>': ')', 
        ':': '-', '"': "'", '?': '', '*': 'X'
    }
    
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    return cleaned.strip()

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
        
        # Template de sortie standard (yt-dlp gère les caractères interdits automatiquement)
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
        'no_warnings': False,  # Activer les warnings pour le debug
        'extract_flat': False,
        
        # Logger personnalisé pour capturer toutes les erreurs
        'logger': logger,
        
        # Hooks de progression et post-processing
        'progress_hooks': [progress_hook],
        'postprocessor_hooks': [post_process_hook],
        
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
    
    # Vérifier si le fichier existe déjà (méthode sécurisée sans glob)
    output_path = Path(output_dir)
    if output_path.exists():
        # Créer plusieurs variantes du titre pour la correspondance
        title_variants = [
            title,  # Titre original
            clean_filename(title),  # Version avec X au lieu de *
            title.replace('***', 'XXX').replace('**', 'XX').replace('*', 'X'),  # Astérisques remplacées par X
            title.replace('*', ''),  # Sans astérisques
            title.replace('*', '_'),  # Astérisques remplacées par underscore
            "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).strip()  # Complètement sanitizé
        ]
        
        # Chercher des fichiers existants qui correspondent à une des variantes
        for existing_file in output_path.iterdir():
            if existing_file.suffix.lower() == '.mp3':
                file_stem_lower = existing_file.stem.lower()
                # Tester chaque variante du titre
                for variant in title_variants:
                    if variant and file_stem_lower.startswith(variant.lower()[:30]):  # Limiter à 30 chars pour éviter les titres trop longs
                        global_stats.add_video_success()
                        return True
    
    ydl_opts = get_ultra_ydl_opts(output_dir)
    
    # Vider la liste des fichiers créés avant le téléchargement
    current_download_files.clear()
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Vérifier que le fichier MP3 final existe vraiment en utilisant le nom capturé
        mp3_found = False
        for filepath in current_download_files:
            if Path(filepath).exists() and Path(filepath).suffix.lower() == '.mp3':
                mp3_found = True
                safe_print(f"✅ MP3 confirmé: {Path(filepath).name}")
                break
        
        if mp3_found:
            global_stats.add_video_success()
            return True
        else:
            global_stats.add_video_failure()
            error_msg = f"[{playlist_name}] Fichier MP3 non trouvé après téléchargement: {title}"
            logger.error(error_msg)
            safe_print(f"❌ {error_msg}")
            return False
        
    except Exception as e:
        global_stats.add_video_failure()
        error_msg = f"[{playlist_name}] Erreur pour {title}: {str(e)}"
        logger.error(error_msg)
        safe_print(f"❌ {error_msg}")
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
    
    # Création du dossier downloads s'il n'existe pas
    downloads_path = Path("downloads")
    downloads_path.mkdir(exist_ok=True)
    
    # Création du dossier playlist avec gestion des conflits
    output_dir = downloads_path / playlist_name
    counter = 1
    while output_dir.exists() and any(output_dir.iterdir()):
        output_dir = downloads_path / f"{playlist_name}_{counter}"
        counter += 1
    
    output_dir.mkdir(exist_ok=True)
    
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

def verify_playlists(playlist_urls):
    """Vérifie et affiche les informations des playlists avant téléchargement"""
    print(f"\n🔍 === VÉRIFICATION DES PLAYLISTS ===")
    
    playlist_infos = []
    for i, url in enumerate(playlist_urls, 1):
        print(f"📋 [{i}/{len(playlist_urls)}] Vérification en cours...")
        
        try:
            playlist_name, entries = extract_playlist_info_fast(url)
            if playlist_name and entries:
                playlist_infos.append({
                    'url': url,
                    'name': playlist_name,
                    'count': len(entries)
                })
                print(f"✅ {playlist_name} ({len(entries)} vidéos)")
            else:
                print(f"❌ Playlist invalide ou vide: {url[:50]}...")
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {str(e)[:50]}...")
    
    if not playlist_infos:
        print("❌ Aucune playlist valide trouvée.")
        return False, []
    
    # Affichage récapitulatif
    print(f"\n📊 === RÉCAPITULATIF ===")
    total_videos = 0
    
    for i, info in enumerate(playlist_infos, 1):
        print(f"🎵 [{i}] {info['name']}")
        print(f"    📹 {info['count']} vidéos")
        print(f"    🔗 {info['url'][:60]}{'...' if len(info['url']) > 60 else ''}")
        total_videos += info['count']
        print()
    
    print(f"📈 TOTAL: {len(playlist_infos)} playlists → {total_videos} vidéos")
    
    # Confirmation utilisateur
    response = input("✅ Continuer le téléchargement ? (O/N): ").strip().lower()
    return response in ['o', 'oui', 'y', 'yes', ''], [info['url'] for info in playlist_infos]

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
    
    # Vérification des playlists avec confirmation
    should_continue, validated_urls = verify_playlists(playlist_urls)
    
    if not should_continue:
        print("⏹️  Téléchargement annulé.")
        return
    
    if not validated_urls:
        print("❌ Aucune playlist valide à télécharger.")
        return
    
    print(f"\n📊 {len(validated_urls)} playlists validées")
    
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
    print(f"   - {len(validated_urls)} playlists")
    print(f"   - {playlist_threads} playlists simultanées")
    print(f"   - {video_threads} threads vidéo par playlist")
    print(f"   - Capacité théorique: {playlist_threads * video_threads} téléchargements simultanés")
    
    input("⏯️  Appuyez sur Entrée pour lancer l'ultra-téléchargement...")
    
    try:
        download_all_playlists_parallel(validated_urls, playlist_threads, video_threads)
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