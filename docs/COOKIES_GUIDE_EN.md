# 🍪 YouTube Premium Cookies Extraction Guide

[🇫🇷 Version française](COOKIES_GUIDE.md)

For the script to access Premium songs, you need to provide your YouTube cookies.

## 📋 Method 1: Browser Extension (RECOMMENDED)

### 1. Install the "Get cookies.txt LOCALLY" extension
- **Chrome**: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- **Firefox**: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

### 2. Log in to YouTube Music
- Go to https://music.youtube.com
- Log in with your Premium account

### 3. Export the cookies
- Click on the extension in your browser
- Click "Export" or "Get cookies.txt"
- Save the file as `cookies.txt` in the script folder

## 📋 Method 2: yt-dlp command line

You can also extract cookies directly with yt-dlp:

```bash
# In your yt/ folder
yt-dlp --cookies-from-browser chrome --cookies cookies.txt --simulate https://music.youtube.com
```

## 🎯 Result

Once the `cookies.txt` file is created in your folder:
```
yt/
├── ultra_downloader.py
├── cookies.txt          ← New file
└── downloads/
```

The script will automatically use your cookies and can download Premium songs!

## ⚠️ Important

- **Never share your cookies.txt file** (contains your credentials)
- The `cookies.txt` file is already in .gitignore
- Renew cookies if they expire (every few months)

## 🔒 Security

Cookies are stored locally and only used by yt-dlp to access YouTube Music with your account.