@echo off
chcp 65001 > nul
title Téléchargeur YouTube Music Ultra-Optimisé


REM Vérifier si l'environnement virtuel existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement Python non trouvé!
    echo    Veuillez d'abord configurer Python et installer yt-dlp
    pause
    exit /b 1
)

REM Lancer le script ultra-optimisé
".venv\Scripts\python.exe" ultra_downloader.py

echo.
echo ✅ Script terminé!
pause