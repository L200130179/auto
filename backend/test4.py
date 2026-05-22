import yt_dlp
import os

v_id = 'NyAopkHYIKg'
url = f"https://www.youtube.com/watch?v={v_id}"
ydl_opts = {
    'quiet': False,
    'skip_download': True,
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['id', 'en'],
    'outtmpl': 'temp_sub'
}
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir('.'):
        if f.startswith('temp_sub'):
            print("Found subtitle file:", f)
            with open(f, 'r', encoding='utf-8') as file:
                print(file.read()[:500])
except Exception as e:
    print("yt-dlp sub fetch failed:", e)
