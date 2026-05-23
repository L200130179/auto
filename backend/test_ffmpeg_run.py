import ffmpeg
import os
import sys

input_video = "static/clip_D_atWzv8Zy4_0.mp4"
output_video_rel = "static/test_ffmpeg_rel.mp4"
output_video_abs = "static/test_ffmpeg_abs.mp4"
output_video_abs_fwd = "static/test_ffmpeg_abs_fwd.mp4"

srt_rel = "static/test_sub.srt"
srt_abs = os.path.abspath(srt_rel)
srt_abs_fwd = srt_abs.replace('\\', '/')

style = "Fontname=Arial,Fontsize=12,PrimaryColour=&H0000FFFF,BorderStyle=1,Outline=1,Shadow=1,MarginV=15,Alignment=2,Bold=1"

# Helper to run ffmpeg-python
def run_ffmpeg(video_filter, output_path):
    in_file = ffmpeg.input(input_video)
    audio = in_file.audio
    out = ffmpeg.output(video_filter, audio, output_path, vcodec='libx264', acodec='copy')
    try:
        # We specify our local ffmpeg.exe for Windows
        local_exe = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
        cmd_path = local_exe if sys.platform == 'win32' and os.path.exists(local_exe) else 'ffmpeg'
        out.run(cmd=cmd_path, overwrite_output=True, quiet=True)
        print(f"SUCCESS: {output_path} generated.")
        return True
    except ffmpeg.Error as e:
        print(f"FAILED: {output_path} failed.")
        if e.stderr:
            print("Stderr snippet:", e.stderr.decode('utf-8')[-300:])
        return False

# 1. Test relative path
print("--- 1. Testing relative path ---")
in_file = ffmpeg.input(input_video)
video = in_file.video.filter('subtitles', srt_rel, force_style=style)
run_ffmpeg(video, output_video_rel)

# 2. Test absolute path (standard Windows path)
print("\n--- 2. Testing absolute path (Windows backslashes) ---")
video = in_file.video.filter('subtitles', srt_abs, force_style=style)
run_ffmpeg(video, output_video_abs)

# 3. Test absolute path with forward slashes
print("\n--- 3. Testing absolute path (forward slashes) ---")
video = in_file.video.filter('subtitles', srt_abs_fwd, force_style=style)
run_ffmpeg(video, output_video_abs_fwd)
