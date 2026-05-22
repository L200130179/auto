import yt_dlp
import os

url = "https://www.youtube.com/watch?v=NyAopkHYIKg"

ops = {
    'quiet': False, 'skip_download': True,
    'writesubtitles': True, 'writeautomaticsub': True,
    'subtitleslangs': ['id', 'en'],
    'subtitlesformat': 'srv1',
    'cookiefile': 'cookies_fixed.txt',
    'js_runtimes': ['node'],
    'outtmpl': 'tempsub_test_js.%(ext)s'
}

with yt_dlp.YoutubeDL(ops) as yd:
    yd.download([url])

print(os.path.exists("tempsub_test_js.id.srv1"))
