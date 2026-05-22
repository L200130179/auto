import google.generativeai as genai
import os
import subprocess

# Generate a fast 10-sec clip of audio from the downloaded video test_audio.m4a
if not os.path.exists("test_clip.mp3"):
    print("Extracting 10s audio...")
    subprocess.run(["ffmpeg", "-y", "-i", "test_audio.m4a", "-t", "10", "test_clip.mp3"], capture_output=True)

print("Uploading to Gemini...")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
model = genai.GenerativeModel("gemini-1.5-flash")

myfile = genai.upload_file("test_clip.mp3")
print("File uploaded:", myfile.name)

prompt = "Transkripsikan audio ini ke dalam format SRT bahasa Indonesia dengan timestamp menit/detik/milisec."
response = model.generate_content([myfile, prompt])
print(response.text)

genai.delete_file(myfile.name)
