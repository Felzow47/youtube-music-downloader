# 🍪 Guide d'extraction des cookies YouTube Premium

Pour que le script puisse accéder aux chansons Premium, vous devez fournir vos cookies YouTube.

## 📋 Méthode 1: Extension de navigateur (RECOMMANDÉ)

### 1. Installez l'extension "Get cookies.txt LOCALLY"
- **Chrome**: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- **Firefox**: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

### 2. Connectez-vous à YouTube Music
- Allez sur https://music.youtube.com
- Connectez-vous avec votre compte Premium

### 3. Exportez les cookies
- Cliquez sur l'extension dans votre navigateur
- Cliquez sur "Export" ou "Get cookies.txt"
- Sauvegardez le fichier sous le nom `cookies.txt` dans le dossier du script

## 📋 Méthode 2: yt-dlp en ligne de commande

Vous pouvez aussi extraire les cookies directement avec yt-dlp :

```bash
# Dans votre dossier yt/
yt-dlp --cookies-from-browser chrome --cookies cookies.txt --simulate https://music.youtube.com
```

## 🎯 Résultat

Une fois le fichier `cookies.txt` créé dans votre dossier :
```
yt/
├── ultra_downloader.py
├── cookies.txt          ← Nouveau fichier
└── downloads/
```

Le script utilisera automatiquement vos cookies et pourra télécharger les chansons Premium !

## ⚠️ Important

- **Ne partagez jamais votre fichier cookies.txt** (contient vos identifiants)
- Le fichier `cookies.txt` est déjà dans le .gitignore
- Renouvelez les cookies si ils expirent (quelques mois)

## 🔒 Sécurité

Les cookies sont stockés localement et ne sont utilisés que par yt-dlp pour accéder à YouTube Music avec votre compte.