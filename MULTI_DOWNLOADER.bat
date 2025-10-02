@echo off
chcp 65001 > nul
title Téléchargeur YouTube Music Multithreadé

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║          🎵 TÉLÉCHARGEUR YOUTUBE MUSIC MULTITHREADÉ 🎵               ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo 🎯 Version équilibrée:
echo    - Une playlist à la fois
echo    - Multithreading optimisé
echo    - Interface utilisateur claire
echo    - MP3 320kbps avec métadonnées
echo.

REM Vérifier si l'environnement virtuel existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement Python non trouvé!
    echo    Veuillez d'abord configurer Python et installer yt-dlp
    pause
    exit /b 1
)

REM Lancer le script multithreadé
".venv\Scripts\python.exe" scripts\multi_threaded_downloader.py

echo.
echo ✅ Script terminé!
pause