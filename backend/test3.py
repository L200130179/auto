from youtube_transcript_api import YouTubeTranscriptApi

try:
    v_id = 'NyAopkHYIKg'
    print(f"Listing transcripts for {v_id}...")
    ts = YouTubeTranscriptApi().list(v_id)
    
    for t in ts:
        print(f"Language: {t.language_code}, is_generated: {t.is_generated}")
        try:
            res = t.fetch()
            print(f"Fetched {len(res)} chunks")
            break # Got one
        except Exception as e:
            print(f"Failed to fetch {t.language_code}: {e}")
            
except Exception as main_e:
    print(f"Failed completely: {main_e}")
