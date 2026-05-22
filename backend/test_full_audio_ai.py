import google.generativeai as genai
import os
import time

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})

print("Uploading 50MB audio to Gemini...")
start = time.time()
audio_file = genai.upload_file("test_audio.m4a")
print(f"Uploaded {audio_file.name} in {time.time()-start:.2f}s")

prompt = """
Kamu adalah analis video TikTok/Reels ahli.
Dengarkan seluruh audio wawancara/podcast ini. Cari tepat 3 "momen emas" (durasi masing-masing persis 30 detik) yang memiliki emosional TERKUAT, hiperbola, argumen paling panas, atau pernyataan paling berani/menantang.
LEWATI bagian *opening*/pembukaan!
Jawab HANYA dengan JSON array:
[
  {
    "title": "Clickbait",
    "start_time": 1500,
    "end_time": 1530,
    "score": "95/100",
    "reason": "Sangat marah"
  }
]
"""
print("Analyzing audio...")
start = time.time()
resp = model.generate_content([audio_file, prompt])
print(f"Analyzed in {time.time()-start:.2f}s")
print(resp.text)

genai.delete_file(audio_file.name)
