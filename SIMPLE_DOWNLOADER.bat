@echo off
chcp 65001 > nul
title Téléchargeur YouTube Music Simple

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║          🎵 TÉLÉCHARGEUR YOUTUBE MUSIC SIMPLE 🎵                ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Version simple et rapide pour une playlist à la fois
echo    - MP3 320kbps
echo    - Interface simplifiée
echo    - Multithreading optimisé
echo.

REM Vérifier si l'environnement virtuel existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement Python non trouvé!
    echo    Veuillez d'abord configurer Python et installer yt-dlp
    pause
    exit /b 1
)

REM Lancer le script simple
".venv\Scripts\python.exe" scripts\simple_downloader.py

echo.
echo ✅ Script terminé!
pause