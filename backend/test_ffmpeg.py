import ffmpeg
import json

in_file = ffmpeg.input('dummy.mp4')
try:
    bg = in_file.video.filter('scale', 1080, 1920, force_original_aspect_ratio='increase').filter('crop', 1080, 1920).filter('boxblur', 20, 20)
    fg = in_file.video.filter('scale', 1080, -1)
    video = ffmpeg.overlay(bg, fg, x='(main_w-overlay_w)/2', y='(main_h-overlay_h)/2')
    out = ffmpeg.output(video, in_file.audio, "out.mp4", vcodec='libx264', acodec='copy')
    print(ffmpeg.compile(out))
except Exception as e:
    import traceback
    traceback.print_exc()
