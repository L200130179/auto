import os
import sys
import yt_dlp
import ffmpeg
import shutil
import google.generativeai as genai
import subprocess

# --- Cross-platform FFmpeg path detection ---
def _get_ffmpeg_path():
    """
    Mendeteksi path FFmpeg secara otomatis:
    - Windows: cari ffmpeg.exe lokal, lalu fallback ke imageio_ffmpeg
    - Linux/Mac: cari 'ffmpeg' di PATH sistem (diinstall via apt/brew)
    """
    if sys.platform == 'win32':
        # Windows: utamakan ffmpeg.exe lokal di folder backend
        local_exe = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
        if os.path.exists(local_exe):
            return local_exe
        # Fallback: gunakan imageio_ffmpeg
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            # Salin ke folder backend agar yt-dlp mudah menemukannya
            if not os.path.exists(local_exe):
                shutil.copy(exe, local_exe)
            return local_exe
        except Exception:
            pass
        return 'ffmpeg'
    else:
        # Linux/Mac: gunakan ffmpeg dari PATH sistem (hasil: apt install ffmpeg)
        system_ffmpeg = shutil.which('ffmpeg')
        if system_ffmpeg:
            return system_ffmpeg
        # Fallback ke imageio_ffmpeg jika ada
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
        return 'ffmpeg'  # Harapkan ada di PATH

FFMPEG_PATH = _get_ffmpeg_path()
print(f"[video_processor] FFmpeg ditemukan di: {FFMPEG_PATH}")

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def create_vertical_clip(url, start_time, end_time, output_dir="static", clip_id="1", transcript_data=None, with_subtitle=True, layout_mode="auto_magic"):
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"clip_{clip_id}.mp4")
    
    # 1. Download the specific segment using yt-dlp (saves time & bandwidth)
    temp_download = os.path.join(output_dir, f"temp_{clip_id}.mp4")
    sub_file = None
    
    # Tentukan direktori ffmpeg untuk yt-dlp (harus berupa folder, bukan path file)
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH) if os.path.isfile(FFMPEG_PATH) else None

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': temp_download,
        'download_ranges': lambda info, ydl: [{'start_time': start_time, 'end_time': end_time}],
        'force_keyframes_at_cuts': True,
        'quiet': False
    }
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir
    
    # 1. Download the specific segment using yt-dlp (saves time & bandwidth)(f"Mengunduh video detik {start_time} - {end_time}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    # Check if download succeeded and get true filename
    actual_temp = temp_download
    for ext in ['.mp4', '.mkv', '.webm']:
        if os.path.exists(f"{temp_download}{ext}"):
            actual_temp = f"{temp_download}{ext}"
            break
            
    if not os.path.exists(actual_temp):
        print(f"Warning: File temp tidak ditemukan! {actual_temp}")
        pass
        
    # Buat file Subtitle (SRT) yang tersinkronisasi sempurna dari transcript_data
    sub_file = None
    if with_subtitle:
        sub_file = os.path.join(output_dir, f"temp_{clip_id}.srt").replace('\\', '/')
        if transcript_data:
            with open(sub_file, 'w', encoding='utf-8') as sf:
                idx = 1
                for i in range(len(transcript_data)):
                    item = transcript_data[i]
                    try:
                        s = float(item['start'])
                        d = float(item['duration'])
                        text = item.get('text', '')
                    except (KeyError, TypeError):
                        s = float(getattr(item, 'start', 0))
                        d = float(getattr(item, 'duration', 0))
                        text = getattr(item, 'text', '')
                        
                    e = s + d
                    
                    # Hindari overlap
                    if i + 1 < len(transcript_data):
                        next_item = transcript_data[i+1]
                        try:
                            next_s = float(next_item['start'])
                        except (KeyError, TypeError):
                            next_s = float(getattr(next_item, 'start', e))
                        if e > next_s: e = next_s
                            
                    # Di dalam klip
                    start_time_fl = float(start_time)
                    end_time_fl = float(end_time)
                    if e >= start_time_fl and s <= end_time_fl:
                        rel_s = max(0, s - start_time_fl)
                        rel_e = min(end_time_fl - start_time_fl, e - start_time_fl)
                        if rel_s >= rel_e: continue
                        s_str = format_srt_time(rel_s)
                        e_str = format_srt_time(rel_e)
                        sf.write(f"{idx}\n{s_str} --> {e_str}\n{text.replace(chr(10), ' ')}\n\n")
                        idx += 1
        else:
            # ULTIMATE FALLBACK: GEMINI AUDIO WHISPER BYPASS
            print("Transcript kosong tapi user minta Subtitle! Mengaktifkan Gemini Audio Whisper...")
            try:
                temp_audio = os.path.join(output_dir, f"temp_audio_{clip_id}.mp3")
                subprocess.run([FFMPEG_PATH, "-y", "-i", actual_temp, "-q:a", "0", "-map", "a", temp_audio], capture_output=True)
                
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                print("Mengupload audio ke Gemini...")
                audio_file = genai.upload_file(temp_audio)
                
                prompt = "Kamu seorang transcriber ahli. Buatkan subtitle berformat SRT murni dalam bahasa Indonesia untuk audio ini. Format waktu mulai dari 00:00:00,000. PASTIKAN SELURUH JAWABAN ANDA HANYA BERISI KODE SRT, TANPA MARKDOWN ATAU KATA PENGANTAR LAIN."
                resp = model.generate_content([audio_file, prompt])
                raw_srt = resp.text.strip()
                if raw_srt.startswith("```"):
                    raw_srt = raw_srt.split("\n", 1)[-1]
                    if raw_srt.endswith("```"): raw_srt = raw_srt[:-3]
                    raw_srt = raw_srt.replace("srt", "", 1).strip()
                    
                with open(sub_file, 'w', encoding='utf-8') as sf:
                    sf.write(raw_srt)
                    
                print("Gemini Audio Whisper selesai!")
                genai.delete_file(audio_file.name)
                os.remove(temp_audio)
            except Exception as e:
                print("Gagal menggunakan Gemini Audio Whisper:", e)
                sub_file = None

    print(f"Memproses video (Cropping 9:16) ke {output_filename}...")
    try:
        in_file = ffmpeg.input(actual_temp)
        
        if layout_mode in ['gaussian_blur', 'auto_magic']:
            # Latar Background Blur, Foreground Asli di Tengah
            bg = in_file.video.filter('scale', 1080, 1920, force_original_aspect_ratio='increase').filter('crop', 1080, 1920).filter('boxblur', 20, 20)
            fg = in_file.video.filter('scale', 1080, -1)
            video = ffmpeg.overlay(bg, fg, x='(main_w-overlay_w)/2', y='(main_h-overlay_h)/2')
        else:
            # Center Crop Dinamis
            video = in_file.video.filter('crop', 'ih*9/16', 'ih').filter('scale', 1080, 1920)
        
        # 3. Hardsub ala TikTok modern (Kecil, Rata Tengah, Margin Bawah)
        if sub_file and os.path.exists(sub_file):
            print("Membakar Subtitle (Sinkronisasi Python):", sub_file)
            style = "Fontname=Arial,Fontsize=12,PrimaryColour=&H0000FFFF,BorderStyle=1,Outline=1,Shadow=1,MarginV=15,Alignment=2,Bold=1"
            video = video.filter('subtitles', sub_file, force_style=style)
            
        audio = in_file.audio
        
        # Compile and run
        out = ffmpeg.output(video, audio, output_filename, vcodec='libx264', acodec='copy')
        out.run(cmd=FFMPEG_PATH, overwrite_output=True, quiet=True)
        print("Pemrosesan Selesai.")
    except Exception as e:
        print("FFmpeg Error:", e)
    finally:
        # Cleanup
        if os.path.exists(actual_temp):
            os.remove(actual_temp)
        if sub_file and os.path.exists(sub_file):
            os.remove(sub_file)
            
    return output_filename
