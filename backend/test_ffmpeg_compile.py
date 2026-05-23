import ffmpeg
import os

in_file = ffmpeg.input('dummy.mp4')

# Relative path with forward slash
sub_rel_forward = 'static/temp_subs.srt'
video_rel = in_file.video.filter('subtitles', sub_rel_forward, force_style="Fontname=Arial")
out_rel = ffmpeg.output(video_rel, in_file.audio, "out.mp4")
print("Relative path forward slash compile:")
print(ffmpeg.compile(out_rel))

# Absolute path with forward slash and escaped colon (which we did manually)
abs_path = os.path.abspath('static/temp_subs.srt').replace('\\', '/')
if ':' in abs_path:
    abs_path = abs_path.replace(':', '\\:', 1)

video_abs = in_file.video.filter('subtitles', abs_path, force_style="Fontname=Arial")
out_abs = ffmpeg.output(video_abs, in_file.audio, "out.mp4")
print("\nAbsolute path forward slash & escaped colon compile:")
print(ffmpeg.compile(out_abs))

# Absolute path with forward slash ONLY (no colon escaping)
abs_path_only_forward = os.path.abspath('static/temp_subs.srt').replace('\\', '/')
video_abs_only_forward = in_file.video.filter('subtitles', abs_path_only_forward, force_style="Fontname=Arial")
out_abs_only_forward = ffmpeg.output(video_abs_only_forward, in_file.audio, "out.mp4")
print("\nAbsolute path forward slash ONLY compile:")
print(ffmpeg.compile(out_abs_only_forward))
