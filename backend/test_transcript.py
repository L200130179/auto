import yt_dlp
import os

url = "https://www.youtube.com/watch?v=NyAopkHYIKg"

ops = {
    'quiet': False, 'skip_download': True,
    'writesubtitles': True, 'writeautomaticsub': True,
    'subtitleslangs': ['id', 'en'],
    'subtitlesformat': 'srv1',
    'cookiefile': 'cookies_fixed.txt',
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    'outtmpl': 'tempsub_test2.%(ext)s'
}

with yt_dlp.YoutubeDL(ops) as yd:
    yd.download([url])

print(os.path.exists("tempsub_test2.id.srv1"))
