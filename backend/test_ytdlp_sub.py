import yt_dlp
import json

url = "https://www.youtube.com/watch?v=o1xsOdtuLRE"
ydl_opts = {
    'quiet': False,
    'skip_download': True,
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['id', 'en'],
    'subtitlesformat': 'json3',
    'outtmpl': 'temp_test.%(ext)s'
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
