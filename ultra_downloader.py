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
import json  # Pour la pause au début

# Créer le dossier logs s'il n'existe pas
Path("logs").mkdir(exist_ok=True)

# Configuration du logging avec fichier unique par session
logger = logging.getLogger("yt_dlp_ultra")
logger.setLevel(logging.INFO)

# Créer un nom de fichier unique avec timestamp (format DD_MM_YY_HHh_MM_SS)
session_timestamp = time.strftime("%d_%m_%y_%Hh_%M_%S")
log_filename = f"logs/ultra_download_{session_timestamp}.log"

# Handler pour fichier d'erreurs de cette session
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# PAS de handler console - on veut seulement les logs dans le fichier
# Les messages normaux seront affichés via print() pour un affichage propre

# Logger pour yt-dlp (capture les erreurs internes)
yt_dlp_logger = logging.getLogger("yt-dlp")
yt_dlp_logger.addHandler(file_handler)

# Logger silencieux pour yt-dlp (aucune sortie)
class SilentLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def info(self, msg): pass

# Verrous pour éviter les conflits
print_lock = threading.Lock()
stats_lock = threading.Lock()

# Dictionnaire pour stocker les lignes de progression actives
active_downloads = {}
download_lock = threading.Lock()

class GlobalStats:
    """Statistiques globales thread-safe"""
    def __init__(self):
        self.playlists_total = 0
        self.playlists_completed = 0
        self.videos_total = 0
        self.videos_completed = 0
        self.videos_failed = 0
        self.start_time = None
        self.failed_videos_by_playlist = {}  # Dict: playlist_name -> [failed_videos]

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

    def add_failed_videos(self, playlist_name, failed_videos):
        with stats_lock:
            if failed_videos:
                self.failed_videos_by_playlist[playlist_name] = failed_videos

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
    """Hook de progression simple - une ligne par téléchargement"""
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', 'N/A').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            filename = os.path.basename(d.get('filename', 'Unknown'))[:40]

            # Afficher uniquement toutes les 5% pour éviter spam
            if percent != 'N/A':
                percent_num = float(percent.replace('%', ''))
                if int(percent_num) % 5 == 0:
                    with print_lock:
                        print(f"📥 {filename}... {percent:>6} à {speed:>12}")
        except:
            pass

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

def cleanup_temp_files(output_path, mp3_filename):
    """Supprime les fichiers temporaires .m4a qui correspondent au MP3"""
    if not mp3_filename:
        return
        
    # Nom de base sans extension
    base_name = Path(mp3_filename).stem
    
    try:
        # Chercher les fichiers .m4a qui ont le même nom de base
        for temp_file in output_path.glob("*.m4a"):
            temp_base = temp_file.stem
            
            # Si le nom correspond (même titre)
            if (base_name.lower() in temp_base.lower() or 
                temp_base.lower() in base_name.lower() or
                base_name.lower()[:20] == temp_base.lower()[:20]):
                
                try:
                    temp_file.unlink()  # Supprimer le fichier silencieusement
                except Exception as e:
                    logger.error(f"Erreur suppression {temp_file}: {e}")
                    
    except Exception as e:
        logger.error(f"Erreur nettoyage temporaires: {e}")

def get_ultra_ydl_opts(output_dir):
    """Configuration ultra-optimisée pour yt-dlp - VITESSE MAXIMALE"""
    opts = {
        # Format audio optimal - préférer m4a (plus rapide, pas de réencodage nécessaire)
        'format': 'bestaudio[ext=m4a]/bestaudio/best',

        # Post-processing pour MP3 320kbps ULTRA-RAPIDE
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],

        # Supprimer les fichiers temporaires après conversion
        'keepvideo': False,
        'keep_video': False,

        # Template de sortie standard (yt-dlp gère les caractères interdits automatiquement)
        'outtmpl': os.path.join(output_dir, '%(title).100s.%(ext)s'),

        # Options de performance MAXIMALES - TURBO MODE
        'concurrent_fragment_downloads': 16,  # 16 fragments parallèles (doublé!)
        'fragment_retries': 3,  # Réduit de 5 à 3 pour ne pas perdre de temps
        'retries': 3,  # Réduit de 5 à 3
        'file_access_retries': 3,  # Réduit de 5 à 3
        'retry_sleep_functions': {'http': lambda n: min(2 * (2 ** n), 15)},  # Retry plus rapide

        # Optimisations réseau TURBO
        'socket_timeout': 30,  # Réduit de 60 à 30s - ne pas attendre trop longtemps
        'http_chunk_size': 33554432,  # 32MB chunks (doublé!) pour télécharger plus gros morceaux
        'buffersize': 32768,  # Buffer doublé

        # Gestion des erreurs - fail fast
        'ignoreerrors': True,
        'no_warnings': True,  # Désactiver les warnings pour gagner du temps
        'extract_flat': False,

        # Logger personnalisé pour capturer toutes les erreurs
        'logger': logger,

        # Hook de progression pour afficher les pourcentages
        'progress_hooks': [progress_hook],

    }
    
    # Ajouter les cookies si le fichier existe
    if Path('cookies.txt').exists():
        opts['cookiefile'] = 'cookies.txt'
    
    return opts

def test_premium_access():
    """
    Teste si l'utilisateur connecté avec les cookies a un accès Premium
    en téléchargeant la DAUBE de Slimane (on déteste ce qu'on fait mais c'est efficace)
    
    IMPORTANT: Slimane c'est les SEULES musiques qu'on a trouvées en Premium-only 
    parce que... je sais pas, il est chiant ? 🤡 Après même s'il est chiant, au moins 
    grâce à ses daubes je peux tester si les cookies Premium fonctionnent ! (Au vu de la vitesse à laquelle ils expirent.)
    Je DÉTESTE Slimane mais toutes ses merdes sont Premium-only, donc c'est le test le plus fiable.
    
    ⚠️  APPEL AUX CONTRIBUTIONS ⚠️
    Si quelqu'un lit ça et utilise ce script et connaît d'autres musiques Premium-only 
    (AUTRE que cette daube de Slimane), MERCI d'ouvrir une issue GitHub ou une pull request 
    avec GRAND PLAISIR ! On sera ravis de remplacer cette merde par autre chose ! 🙏
    
    On télécharge juste pour tester puis à la MILLISECONDE où on a le résultat 
    on supprime cette MERDE ! 🔥💀 Pas question de garder Slimane une seconde de plus !
    SLIMANE = NECESSARY EVIL pour tester Premium. Désolé pas désolé.
    """
    if not Path('cookies.txt').exists():
        return False, "❌ Aucun fichier cookies.txt trouvé"
    
    
    
    # URLs de test Premium-only - ATTENTION : C'EST DU SLIMANE ! 🤮
    # JE DÉTESTE cette merde de Slimane mais c'est le seul moyen de tester Premium
    # Toutes ses musiques sont Premium-only,il nous force à utiliser ses daubes
    # On télécharge juste pour tester puis on supprime immédiatement cette merde
    premium_test_urls = [
        "https://music.youtube.com/watch?v=2TaiYw83ZgQ",  # Slimane - Mise à jour (JE DÉTESTE CETTE MERDE)
        "https://music.youtube.com/watch?v=_sUak2xdxWQ",  # Slimane - La vie est belle (QUEL TITRE IRONIQUE)
        "https://music.youtube.com/watch?v=Yudzx2GmbQw",  # Slimane - La recette (ENCORE CETTE MERDE)
        "https://music.youtube.com/watch?v=9oDnPZV7nYc",  # Slimane - Bye Bye (OUI BYE BYE SLIMANE !)
    ]
    
    # Créer un dossier temporaire pour le test
    test_dir = Path("temp_premium_test")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Hook de progression silencieux pour le test (on veut pas voir le nom de Slimane !)
        def silent_progress_hook(d):
            pass  # On affiche rien, on veut pas voir cette merde de Slimane !
        
        # Configuration pour téléchargement RÉEL mais rapide et SILENCIEUX
        test_opts = get_ultra_ydl_opts(str(test_dir))
        test_opts.update({
            'format': 'worst[ext=m4a]/worst[filesize<2M]/worst',  # Format encore plus petit
            'postprocessors': [],  # Pas de conversion MP3 pour le test
            'quiet': False,  # Voir les erreurs mais pas la progression
            'ignoreerrors': False,  # IMPORTANT: Ne pas ignorer les erreurs Premium !
            'progress_hooks': [silent_progress_hook],  # Hook silencieux pour masquer Slimane
            # Timeouts ultra courts pour test rapide
            'socket_timeout': 15,  # 15s au lieu de 60s
            'fragment_retries': 2,  # 2 au lieu de 5
            'retries': 2,  # 2 au lieu de 5
            'file_access_retries': 2,  # 2 au lieu de 5
            'logger': SilentLogger(),  # Désactive tous les logs yt-dlp pendant le test
        })
        
        # Variables partagées pour les threads
        premium_success_count = 0
        premium_blocked_count = 0
        test_lock = threading.Lock()
        completed_tests = 0
        
        def test_single_url(test_url, test_num):
            """Teste une seule URL Premium en thread séparé"""
            nonlocal premium_success_count, premium_blocked_count, completed_tests
            
            try:
                with yt_dlp.YoutubeDL(test_opts) as ydl:
                    # VRAIMENT télécharger cette merde de Slimane (désolé mais c'est le seul moyen de tester Premium)
                    # On déteste ce qu'on fait mais c'est pour la science !
                    ydl.download([test_url])
                    
                    # Vérifier si un fichier a été téléchargé = Premium confirmé
                    downloaded_files = list(test_dir.glob("*"))
                    if downloaded_files:
                        with test_lock:
                            premium_success_count += 1
                        
                        # Supprimer ce fichier de merde immédiatement - on ne garde pas Slimane !
                        for file in downloaded_files:
                            try:
                                file.unlink()  # BURN SLIMANE BURN! 🔥
                            except:
                                pass
                        return True
                    else:
                        with test_lock:
                            premium_blocked_count += 1
                        return False
                        
            except:
                # Toute erreur = pas Premium
                with test_lock:
                    premium_blocked_count += 1
                return False

        # Lancer les tests en parallèle avec ThreadPoolExecutor
        # Affichage coloré sans horodatage pour les tests Premium
        print(f"\033[92m🚀 Lancement de {len(premium_test_urls)} tests simultanés...\033[0m")
        print("  \033[96m🔍 Test de l'accès Premium en cours...\033[0m")

        with ThreadPoolExecutor(max_workers=4) as executor:
            # Lancer tous les tests en parallèle
            futures = []
            for i, test_url in enumerate(premium_test_urls, 1):
                future = executor.submit(test_single_url, test_url, i)
                futures.append(future)

            # Afficher la progression en temps réel
            while completed_tests < len(premium_test_urls):
                time.sleep(0.1)  # Check toutes les 100ms
                current_completed = sum(1 for f in futures if f.done())
                if current_completed > completed_tests:
                    completed_tests = current_completed
                    progress = (completed_tests / len(premium_test_urls)) * 100
                    print(f"\r   📊 Progression: {completed_tests}/{len(premium_test_urls)} ({progress:.0f}%)", end='', flush=True)

            print()  # Nouvelle ligne après la progression

            # Collecter les résultats
            results = []
            for future in futures:
                try:
                    results.append(future.result())
                except Exception:
                    results.append(False)

        # Nettoyer le dossier de test
        try:
            for file in test_dir.glob("*"):
                file.unlink()
            test_dir.rmdir()
        except:
            pass
        
        # Plus d'explications dans les commentaires du code si besoin
        
        # Analyse des résultats RÉELS (avec la daube de Slimane malheureusement)
        if premium_success_count > 0:
            return True, f"✅ PREMIUM CONFIRMÉ ! Test réussi {premium_success_count}/{len(premium_test_urls)} fois"
        
        elif premium_blocked_count > 0:
            return False, f"❌ PAS DE PREMIUM ! Contenu bloqué {premium_blocked_count}/{len(premium_test_urls)} fois"
        
        else:
            return False, "❌ Test impossible - Erreur de connexion"
            
    except Exception as e:
        # Nettoyer en cas d'erreur
        try:
            for file in test_dir.glob("*"):
                file.unlink()
            test_dir.rmdir()
        except:
            pass
        return False, f"❌ Erreur critique lors du test: {str(e)[:50]}..."

def download_single_video(video_info, output_dir, playlist_name):
    """Télécharge une seule vidéo avec gestion d'erreur optimisée et vérification ultra-rapide du MP3 généré"""
    video_id = video_info.get('id')
    title = video_info.get('title', 'Unknown')[:50]
    url = f"https://www.youtube.com/watch?v={video_id}"

    output_path = Path(output_dir)
    # Vérifier si le fichier existe déjà (méthode sécurisée sans glob)
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
        for existing_file in output_path.iterdir():
            if existing_file.suffix.lower() == '.mp3':
                file_stem_lower = existing_file.stem.lower()
                for variant in title_variants:
                    if variant and file_stem_lower.startswith(variant.lower()[:30]):
                        global_stats.add_video_success()
                        return True

    # Utiliser un hook pour récupérer le nom du fichier MP3 final
    final_mp3 = {'filename': None}

    def mp3_postprocessor_hook(d):
        """Hook appelé après la conversion MP3"""
        if d['status'] == 'finished':
            final_mp3['filename'] = d.get('info_dict', {}).get('filepath') or d.get('filepath')

    def progress_final_hook(d):
        """Hook pour capturer le fichier final téléchargé"""
        if d['status'] == 'finished':
            if not final_mp3['filename']:
                final_mp3['filename'] = d.get('filename')

    ydl_opts = get_ultra_ydl_opts(output_dir)
    ydl_opts = dict(ydl_opts)  # Copie défensive
    ydl_opts['postprocessor_hooks'] = [mp3_postprocessor_hook]
    # Garder le progress_hook d'origine + ajouter progress_final_hook
    ydl_opts['progress_hooks'] = [progress_hook, progress_final_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        mp3_file_path = None
        if final_mp3['filename']:
            mp3_file_path = Path(final_mp3['filename'])
        else:
            # Fallback : essayer de retrouver le fichier par titre si le hook n'a pas marché
            for mp3_file in output_path.glob("*.mp3"):
                if clean_filename(title).lower() in mp3_file.stem.lower():
                    mp3_file_path = mp3_file
                    break

        if mp3_file_path and mp3_file_path.exists():
            # MP3 validé
            file_size = mp3_file_path.stat().st_size / (1024 * 1024)
            with print_lock:
                print(f"✅ MP3 validé: {mp3_file_path.name[:50]} ({file_size:.1f} MB)")

            try:
                cleanup_temp_files(output_path, mp3_file_path.name)
            except:
                pass
            global_stats.add_video_success()
            return True
        else:
            global_stats.add_video_failure()
            with print_lock:
                print(f"❌ Échec validation MP3: {title[:50]}")
            logger.error(f"[{playlist_name}] MP3 non trouvé: {title}")
            return False

    except Exception as e:
        global_stats.add_video_failure()
        error_str = str(e).lower()
        if "music premium members" in error_str or "premium members" in error_str:
            logger.error(f"[{playlist_name}] PREMIUM REQUIS: {title}")
        elif "private" in error_str or "unavailable" in error_str:
            logger.error(f"[{playlist_name}] INDISPONIBLE: {title}")
        else:
            logger.error(f"[{playlist_name}] ERREUR: {title} - {str(e)}")
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
    completed_count = 0

    # Téléchargement parallèle - seulement barres individuelles
    with ThreadPoolExecutor(max_workers=video_threads) as executor:
        futures = {}
        for video_info in entries:
            future = executor.submit(download_single_video, video_info, output_dir, playlist_name)
            futures[future] = video_info.get('title', 'Unknown')[:50]

        # Collecter les résultats silencieusement
        failed_videos = []
        for future in as_completed(futures):
            video_title = futures[future]
            try:
                if future.result():
                    success_count += 1
                else:
                    failed_videos.append(video_title)
            except Exception as e:
                failed_videos.append(video_title)
                logger.error(f"[{playlist_name}] Exception: {str(e)}")

    print()  # Saut de ligne après les téléchargements

    # Vérifier RÉELLEMENT les MP3 dans le dossier
    actual_mp3_files = list(output_dir.glob("*.mp3"))
    actual_mp3_count = len(actual_mp3_files)

    global_stats.complete_playlist()

    # Sauvegarder les infos pour les stats finales
    global_stats.add_failed_videos(playlist_name, failed_videos)

    return True

def download_all_playlists_parallel(playlist_urls, playlist_threads=3, video_threads_per_playlist=6):
    """Télécharge toutes les playlists en parallèle"""
    with print_lock:
        print(f"\033[92m🚀 DÉMARRAGE ULTRA-OPTIMISÉ\033[0m")
        print(f"\033[94m📊 {len(playlist_urls)} playlists, {playlist_threads} playlists simultanées\033[0m")
        print(f"\033[95m⚙️  {video_threads_per_playlist} threads vidéo par playlist\033[0m")
    
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
                    with print_lock:
                        print(f"\033[92m🎉 Playlist {playlist_num}/{len(playlist_urls)} terminée avec succès\033[0m")
                else:
                    with print_lock:
                        print(f"\033[91m❌ Playlist {playlist_num}/{len(playlist_urls)} échouée\033[0m")
            except Exception as e:
                with print_lock:
                    print(f"\033[91m❌ Erreur critique playlist {playlist_num}: {str(e)}\033[0m")
                logger.error(f"Erreur critique playlist {playlist_url}: {str(e)}")

def print_final_stats():
    """Affiche les statistiques finales avec musiques manquantes"""
    playlists_done, playlists_total, videos_done, videos_failed, videos_total = global_stats.get_stats()
    elapsed = time.time() - global_stats.start_time

    safe_print(f"\n\033[95m{'='*60}\033[0m")
    safe_print(f"\033[93m🎉 === STATISTIQUES FINALES ===\033[0m")
    safe_print(f"\033[95m{'='*60}\033[0m")
    safe_print(f"\033[94m📋 Playlists: {playlists_done}/{playlists_total} terminées\033[0m")
    safe_print(f"\033[92m🎵 Vidéos: {videos_done}/{videos_total} réussies\033[0m")
    safe_print(f"\033[91m❌ Échecs: {videos_failed}\033[0m")
    safe_print(f"\033[94m⏱️  Temps total: {elapsed:.1f}s\033[0m")
    safe_print(f"\033[95m🚀 Vitesse: {videos_done/elapsed:.2f} vidéos/seconde\033[0m")
    safe_print(f"\033[92m💪 Efficacité: {(videos_done/videos_total)*100:.1f}%\033[0m")

    # Afficher les musiques manquantes par playlist
    if global_stats.failed_videos_by_playlist:
        safe_print(f"\n\033[91m📋 Musiques manquantes:\033[0m")
        for playlist_name, failed_videos in global_stats.failed_videos_by_playlist.items():
            if failed_videos:
                safe_print(f"\033[93m[{playlist_name}]\033[0m")
                for i, failed_title in enumerate(failed_videos, 1):
                    safe_print(f"\033[91m  {i}. {failed_title}\033[0m")
                safe_print("")
        safe_print(f"\033[96m💡 Détails des erreurs dans: logs/{log_filename}\033[0m")

    safe_print(f"\033[95m{'='*60}\033[0m")

def verify_playlists(playlist_urls):
    """Vérifie et affiche les informations des playlists avant téléchargement"""
    print(f"\n\033[95m🔍 === VÉRIFICATION DES PLAYLISTS ===\033[0m")
    
    playlist_infos = []
    for i, url in enumerate(playlist_urls, 1):
        print(f"\033[93m📋 [{i}/{len(playlist_urls)}] Vérification en cours...\033[0m")
        
        try:
            playlist_name, entries = extract_playlist_info_fast(url)
            if playlist_name and entries:
                playlist_infos.append({
                    'url': url,
                    'name': playlist_name,
                    'count': len(entries)
                })
                print(f"\033[92m✅ {playlist_name} ({len(entries)} vidéos)\033[0m")
            else:
                print(f"\033[91m❌ Playlist invalide ou vide: {url[:50]}...\033[0m")
                
        except Exception as e:
            print(f"\033[91m❌ Erreur lors de la vérification: {str(e)[:50]}...\033[0m")
    
    if not playlist_infos:
        print("\033[91m❌ Aucune playlist valide trouvée.\033[0m")
        return False, []
    
    # Affichage récapitulatif
    print(f"\n\033[95m📊 === RÉCAPITULATIF ===\033[0m")
    total_videos = 0
    
    for i, info in enumerate(playlist_infos, 1):
        print(f"\033[92m🎵 [{i}] {info['name']}\033[0m")
        print(f"\033[94m    📹 {info['count']} vidéos\033[0m")
        print(f"\033[95m    🔗 {info['url'][:60]}{'...' if len(info['url']) > 60 else ''}\033[0m")
        total_videos += info['count']
        print()
    
    print(f"\033[93m📈 TOTAL: {len(playlist_infos)} playlists → {total_videos} vidéos\033[0m")
    
    # Confirmation utilisateur
    response = input("\033[92m✅ Continuer le téléchargement ? (O/N): \033[0m").strip().lower()
    return response in ['o', 'oui', 'y', 'yes', ''], [info['url'] for info in playlist_infos]

def cleanup_old_logs():
    """Garde seulement les 5 logs les plus récents (format DD_MM_YY_HHh_MM_SS)"""
    try:
        logs_path = Path("logs")
        if not logs_path.exists():
            return
            
        # Récupérer tous les logs ultra_download avec le nouveau format
        log_files = list(logs_path.glob("ultra_download_*.log"))
        
        if len(log_files) <= 5:
            return  # Pas besoin de nettoyer
            
        # Trier par date de modification (plus récent en premier)
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Garder les 5 plus récents, supprimer le reste
        logs_to_delete = log_files[5:]
        
        for log_file in logs_to_delete:
            try:
                log_file.unlink()
                print(f"\033[93m🧹 Log ancien supprimé: {log_file.name}\033[0m")
            except Exception:
                pass  # Ignore si on ne peut pas supprimer
                
        if logs_to_delete:
            print(f"\033[92m🗂️  Nettoyage terminé: {len(logs_to_delete)} anciens logs supprimés\033[0m")
            print(f"\033[94m📁 {len(log_files) - len(logs_to_delete)} logs conservés\033[0m")
                    
    except Exception as e:
        print(f"\033[91m⚠️ Erreur lors du nettoyage des logs: {e}\033[0m")
        pass  # Ignore les erreurs de nettoyage

def main():
    """Fonction principale ultra-optimisée"""
    # Écran de démarrage ULTRA STYLÉ
    print("\033[95m" + "=" * 80)
    print("██╗   ██╗██╗  ████████╗██████╗  █████╗     ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  █████╗ ██████╗ ███████╗██████╗ ")
    print("██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗")  
    print("██║   ██║██║     ██║   ██████╔╝███████║    ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║███████║██║  ██║█████╗  ██████╔╝")
    print("██║   ██║██║     ██║   ██╔══██╗██╔══██║    ██║  ██║██║   ██║██║███╗██║██║╚██╗██║██║     ██║   ██║██╔══██║██║  ██║██╔══╝  ██╔══██╗")
    print("╚██████╔╝███████╗██║   ██║  ██║██║  ██║    ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝██║  ██║██████╔╝███████╗██║  ██║")
    print(" ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝")
    print("\033[0m")
    print("\033[96m" + "=" * 80 + "\033[0m")
    print()
    print("\033[93m🎵 YOUTUBE MUSIC DOWNLOADER - VERSION ULTRA-OPTIMISÉE 🎵\033[0m")
    print("\033[92m" + "─" * 80 + "\033[0m")
    print()
    print("\033[91m⚡ PERFORMANCES MAXIMALES:\033[0m")
    print("   \033[94m🚀 Playlists téléchargées en PARALLÈLE\033[0m")
    print("   \033[94m🔥 Multithreading par playlist\033[0m") 
    print("   \033[94m🎧 MP3 320kbps avec métadonnées COMPLÈTES\033[0m")
    print("   \033[94m🧠 Gestion intelligente des doublons\033[0m")
    print("   \033[94m📊 Logging complet des erreurs\033[0m")
    print("   \033[94m🍪 Support Premium avec cookies\033[0m")
    print()
    time.sleep(3)  # Pause de 3 secondes pour profiter du beau ascii art et mon script kiddes :D XD
    print(f"\033[95m📝 Logs de cette session: {log_filename}\033[0m")  
    # Nettoyer les anciens logs après avoir affiché le nom du nouveau
    cleanup_old_logs()
    print("\033[95m" + "=" * 80)
    print()
    
    # Vérification des cookies d'authentification
    if Path('cookies.txt').exists():
        print("\033[93m🍪 Cookies YouTube détectés - Test de l'accès Premium...\033[0m")
        #logger.info("🍪 Cookies YouTube détectés et chargés pour l'authentification Premium")
        
        # Tester l'accès Premium
        is_premium, message = test_premium_access()
        print(f"   \033[94m{message}\033[0m")
        
        if is_premium:
            print("\033[92m     ✅ Prêt pour télécharger du contenu Premium !\033[0m")
            #logger.info("✅ Accès Premium confirmé par le test")
        else:
            print("\033[91m     ⚠️  Accès limité - Certaines chansons Premium pourraient échouer lors du téléchargement\033[0m")
            logger.warning("❌ Test Premium échoué - Cookies peut-être expirés")
            
    else:
        print("\033[94mℹ️  Pas de cookies détectés - Certaines chansons Premium pourraient échouer\033[0m")
        print("\033[95m📖 Consultez https://github.com/Felzow47/youtube-music-downloader/blob/main/docs/COOKIES_GUIDE.md pour configurer l'accès Premium\033[0m")
        #logger.info("ℹ️  Aucun fichier cookies.txt trouvé - Mode public uniquement")
    print()
    
    # Saisie des URLs
    print("\033[93m📝 Collez vos URLs de playlists YouTube Music (séparées par des virgules):\033[0m")
    raw_input = input("\033[95m🔗 URLs: \033[0m").strip()
    
    if not raw_input:
        print("\033[91m❌ Aucune URL fournie.\033[0m")
        return
    
    playlist_urls = [url.strip() for url in raw_input.split(',') if url.strip()]
    
    if not playlist_urls:
        print("\033[91m❌ Aucune URL valide.\033[0m")
        return
    
    # Vérification des playlists avec confirmation
    should_continue, validated_urls = verify_playlists(playlist_urls)
    
    if not should_continue:
        print("\033[93m⏹️  Téléchargement annulé.\033[0m")
        return
    
    if not validated_urls:
        print("\033[91m❌ Aucune playlist valide à télécharger.\033[0m")
        return
    
    print(f"\n\033[92m📊 {len(validated_urls)} playlists validées\033[0m")
    
    # Configuration avancée
    try:
        playlist_threads = int(input("\033[95m🔀 Playlists simultanées (recommandé 2-3): \033[0m") or "2")
        playlist_threads = max(1, min(playlist_threads, 4))
    except ValueError:
        playlist_threads = 2
    
    try:
        video_threads = int(input("\033[95m⚙️  Threads vidéo par playlist (recommandé 6-8): \033[0m") or "6")
        video_threads = max(1, min(video_threads, 12))
    except ValueError:
        video_threads = 6
    
    print(f"\n\033[93m🎯 Configuration finale:\033[0m")
    print(f"\033[94m   - {len(validated_urls)} playlists\033[0m")
    print(f"\033[94m   - {playlist_threads} playlists simultanées\033[0m")
    print(f"\033[94m   - {video_threads} threads vidéo par playlist\033[0m")
    print(f"\033[92m   - Capacité théorique: {playlist_threads * video_threads} téléchargements simultanés\033[0m")
    
    input("\033[95m⏯️  Appuyez sur Entrée pour lancer l'ultra-téléchargement...\033[0m")
    
    try:
        download_all_playlists_parallel(validated_urls, playlist_threads, video_threads)
        print_final_stats()
        
    except KeyboardInterrupt:
        print("\n\033[93m⏹️  Arrêt demandé par l'utilisateur\033[0m")
        print_final_stats()
    except Exception as e:
        print(f"\n\033[91m❌ Erreur critique: {str(e)}\033[0m")
        logger.error(f"Erreur critique main: {str(e)}")
        print_final_stats()

if __name__ == "__main__":
    main()