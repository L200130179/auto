import youtube_transcript_api
print("Module dir:", dir(youtube_transcript_api))
from youtube_transcript_api import YouTubeTranscriptApi
print("Class dir:", dir(YouTubeTranscriptApi))
try:
    print(YouTubeTranscriptApi.get_transcript('NyAopkHYIKg', languages=['id', 'en']))
except Exception as e:
    import traceback
    traceback.print_exc()
