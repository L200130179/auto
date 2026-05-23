import subprocess
import os
import sys
from video_processor import _get_ffmpeg_path

ffmpeg_path = _get_ffmpeg_path()
input_video = "static/clip_D_atWzv8Zy4_0.mp4"
output_video_explicit = "static/test_ffmpeg_explicit.mp4"
srt_abs = os.path.abspath("static/test_sub.srt")

# Format absolute path: replace backslashes with forward slashes and escape colon
srt_abs_escaped = srt_abs.replace('\\', '/')
if ':' in srt_abs_escaped:
    srt_abs_escaped = srt_abs_escaped.replace(':', '\\:', 1)

print("Escaped path:", srt_abs_escaped)

# Construct filter with explicit filename= and single quotes around path
style = "Fontname=Arial,Fontsize=12,PrimaryColour=&H0000FFFF,BorderStyle=1,Outline=1,Shadow=1,MarginV=15,Alignment=2,Bold=1"

# We must escape the single quotes and colons for the filter argument
# Let's try two styles of filter strings:
# Style A: subtitles=filename='E\:/path/to/file.srt':force_style='...'
filter_a = f"subtitles=filename='{srt_abs_escaped}':force_style='{style}'"

cmd = [
    ffmpeg_path,
    "-y",
    "-i", input_video,
    "-vf", filter_a,
    "-acodec", "copy",
    output_video_explicit
]

print("Running command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if res.returncode != 0:
    print("Stderr snippet:")
    print(res.stderr[-500:])
else:
    print("SUCCESS!")
