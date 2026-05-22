import http.cookiejar
import requests
from youtube_transcript_api import YouTubeTranscriptApi

v_id = "NyAopkHYIKg"
session = requests.Session()
cj = http.cookiejar.MozillaCookieJar('cookies_fixed.txt')
cj.load(ignore_discard=True, ignore_expires=True)
session.cookies.update(cj)
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8"
})

try:
    api = YouTubeTranscriptApi(http_client=session)
    data = api.get_transcript(v_id, languages=['id', 'en'])
    print("SUCCESS!", len(data))
except Exception as e:
    print("ERROR:", repr(e))
