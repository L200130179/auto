import os
import subprocess
import sys
from video_processor import _get_ffmpeg_path

ffmpeg_path = _get_ffmpeg_path()
print("FFmpeg path:", ffmpeg_path)

input_video = os.path.abspath("static/clip_D_atWzv8Zy4_0.mp4")
output_video = os.path.abspath("static/test_sub_output_abs.mp4")
srt_file = os.path.abspath("static/test_sub_abs.srt")

# Write a simple SRT file
with open(srt_file, "w", encoding="utf-8") as f:
    f.write("1\n00:00:00,000 --> 00:00:05,000\nTesting Absolute Subtitles Burn-in!\n\n")

print(f"SRT file created: {os.path.exists(srt_file)}")

# Cross-platform escaping function
def escape_path_for_ffmpeg(path_str):
    abs_path = os.path.abspath(path_str)
    if sys.platform == 'win32':
        path_escaped = abs_path.replace('\\', '/')
        if ':' in path_escaped:
            path_escaped = path_escaped.replace(':', '\\:', 1)
        return path_escaped
    else:
        path_escaped = abs_path.replace('\\', '\\\\')
        path_escaped = path_escaped.replace(':', '\\:')
        path_escaped = path_escaped.replace(',', '\\,')
        path_escaped = path_escaped.replace('[', '\\[')
        path_escaped = path_escaped.replace(']', '\\]')
        return path_escaped

sub_file_param = escape_path_for_ffmpeg(srt_file)
print("Escaped path parameter:", sub_file_param)

style = "Fontname=Arial,Fontsize=12,PrimaryColour=&H0000FFFF,BorderStyle=1,Outline=1,Shadow=1,MarginV=15,Alignment=2,Bold=1"

cmd = [
    ffmpeg_path,
    "-y",
    "-i", input_video,
    "-vf", f"subtitles={sub_file_param}:force_style='{style}'",
    "-acodec", "copy",
    output_video
]

print("Running command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("Success! File generated at:", output_video)
