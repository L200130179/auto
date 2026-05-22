import os
import json
import http.cookiejar
import requests
from youtube_transcript_api import YouTubeTranscriptApi

v_id = "o1xsOdtuLRE"

session = None
if os.path.exists('cookies_fixed.txt'):
    session = requests.Session()
    cj = http.cookiejar.MozillaCookieJar('cookies_fixed.txt')
    try:
        cj.load(ignore_discard=True, ignore_expires=True)
        session.cookies.update(cj)
        print("Cookie jar loaded for youtube_transcript_api.")
    except Exception as e:
        print("Gagal load cookies_fixed.txt untuk API:", e)

try:
    api = YouTubeTranscriptApi(http_client=session) if session else YouTubeTranscriptApi()
    data = api.fetch(v_id, languages=['id', 'en', 'en-US'])
    print("SUCCESS! Transcripts loaded. Count:", len(data))
    print("Sample:", data[:2])
    with open('debug_transcript.json', 'w') as f:
        json.dump(data, f)
except Exception as e:
    print("ERROR API:", repr(e))
