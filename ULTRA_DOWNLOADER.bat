@echo off
chcp 65001 > nul
title Téléchargeur YouTube Music Ultra-Optimisé

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║          🎵 TÉLÉCHARGEUR YOUTUBE MUSIC ULTRA-OPTIMISÉ 🎵             ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo ⚡ PERFORMANCES MAXIMALES:
echo    - Playlists téléchargées en parallèle
echo    - Multithreading par playlist  
echo    - MP3 320kbps avec métadonnées
echo    - Gestion intelligente des doublons
echo.

REM Vérifier si l'environnement virtuel existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement Python non trouvé!
    echo    Veuillez d'abord configurer Python et installer yt-dlp
    pause
    exit /b 1
)

REM Lancer le script ultra-optimisé
".venv\Scripts\python.exe" scripts\ultra_downloader.py

echo.
echo ✅ Script terminé!
pause