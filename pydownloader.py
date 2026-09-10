
#!/usr/bin/env python3

import os, sys, subprocess, shutil, re
from urllib.parse import urlparse, parse_qs, unquote

def ensure(pkg, pip=None):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip or pkg])

ensure("requests")
ensure("yt_dlp","yt-dlp")

import requests
import yt_dlp

DOWNLOAD_DIR="downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

IMAGE_EXTS=(".jpg",".jpeg",".png",".gif",".webp",".bmp",".svg")

def clean(name):
    return re.sub(r'[<>:"/\\\\|?*]',"",name)

def ffmpeg():
    return shutil.which("ffmpeg")

def google(url):
    p=urlparse(url)
    if "google." in p.netloc and p.path=="/imgres":
        q=parse_qs(p.query)
        if "imgurl" in q:
            return unquote(q["imgurl"][0])
    return url

def image(url):
    url=google(url)
    fn=clean(os.path.basename(urlparse(url).path) or "image.jpg")
    path=os.path.join(DOWNLOAD_DIR,fn)
    r=requests.get(url,stream=True,timeout=30)
    r.raise_for_status()
    with open(path,"wb") as f:
        for c in r.iter_content(8192):
            if c: f.write(c)
    print("Saved:",path)

def hook(d):
    if d["status"]=="downloading":
        print("\r",d.get("_percent_str",""),d.get("_speed_str",""),end="")
    elif d["status"]=="finished":
        print("\nProcessing...")

def ytdlp(url,audio=False,thumb=False):
    opts={
      "outtmpl":os.path.join(DOWNLOAD_DIR,"%(title)s.%(ext)s"),
      "noplaylist":True,
      "progress_hooks":[hook],
      "extractor_args":{"youtube":{"player_client":["android","web"]}},
      "retries":10,
      "fragment_retries":10,
      "continuedl":True,
    }
    if thumb:
        opts["skip_download"]=True
        opts["writethumbnail"]=True
        opts["convertthumbnails"]="jpg"
    elif audio:
        opts["format"]="bestaudio/best"
        if ffmpeg():
            opts["postprocessors"]=[{
              "key":"FFmpegExtractAudio",
              "preferredcodec":"mp3",
              "preferredquality":"192"}]
    else:
        if ffmpeg():
            opts["format"]="bv*+ba/bestvideo+bestaudio/best"
            opts["merge_output_format"]="mp4"
        else:
            opts["format"]="best"
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

def download(url,audio=False,thumb=False):
    url=google(url)
    if urlparse(url).path.lower().endswith(IMAGE_EXTS):
        image(url)
    else:
        ytdlp(url,audio,thumb)

def menu():
    while True:
        print("""
PyDownloader v4.0

1. Download Video
2. Download Audio (MP3)
3. Download Thumbnail
4. Automatic Download
5. Quit
""")
        c=input("Choice: ").strip()
        if c=="5":
            break
        url=input("URL: ").strip()
        if not url.startswith(("http://","https://")):
            print("Invalid URL")
            continue
        if c=="1":
            download(url)
        elif c=="2":
            download(url,audio=True)
        elif c=="3":
            download(url,thumb=True)
        elif c=="4":
            download(url)
        else:
            print("Invalid choice")

if __name__=="__main__":
    menu()

