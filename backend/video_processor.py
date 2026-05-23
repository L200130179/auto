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

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def get_ass_header():
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,42,&H0000FFFF,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,10,10,300,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
def srt_to_ass(srt_text):
    import re
    srt_text = srt_text.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    dialogues = []
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 3:
            continue
        time_line = lines[1]
        if '-->' not in time_line:
            found_time = False
            for idx, line in enumerate(lines):
                if '-->' in line:
                    time_line = line
                    text_lines = lines[idx+1:]
                    found_time = True
                    break
            if not found_time:
                continue
        else:
            text_lines = lines[2:]
            
        time_match = re.match(r'(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)', time_line)
        if not time_match:
            continue
            
        start_srt, end_srt = time_match.groups()
        
        def convert_time(t_str):
            parts = t_str.replace(',', '.').split(':')
            h = int(parts[0])
            m = int(parts[1])
            s_float = float(parts[2])
            total_seconds = h * 3600 + m * 60 + s_float
            return format_ass_time(total_seconds)
            
        start_ass = convert_time(start_srt)
        end_ass = convert_time(end_srt)
        
        text = " ".join(text_lines)
        text = re.sub(r'<[^>]+>', '', text)
        dialogues.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")
        
    return get_ass_header() + "\n".join(dialogues)

def get_cookie_file():
    """
    Melacak cookies_fixed.txt atau cookies.txt di backend folder
    """
    backend_dir = os.path.dirname(__file__)
    for filename in ['cookies_fixed.txt', 'cookies.txt']:
        cookie_path = os.path.join(backend_dir, filename)
        if os.path.exists(cookie_path):
            return cookie_path
    return None

def get_gemini_keys():
    raw = os.getenv("GEMINI_API_KEY", "")
    return [k.strip() for k in raw.replace(';', ',').split(',') if k.strip() and k.strip() != "YOUR_GEMINI_API_KEY"]

def call_gemini_with_rotation(func, *args, **kwargs):
    keys = get_gemini_keys()
    if not keys:
        raise Exception("Tidak ada API Key Gemini yang terkonfigurasi.")
    last_err = None
    for key in keys:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            return func(genai, *args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "exhausted" in err_str or "rate limit" in err_str:
                print(f"[Gemini Rotation] Key {key[:8]}... habis kuota (429). Mencoba key berikutnya...")
                last_err = e
                continue
            else:
                print(f"[Gemini Rotation] Key {key[:8]}... gagal dengan error: {e}. Mencoba key berikutnya...")
                last_err = e
                continue
    raise last_err if last_err else Exception("Seluruh API Key Gemini gagal.")

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
    
    # Try downloading segment without cookies first, fallback to cookies if it fails
    print(f"Mengunduh video detik {start_time} - {end_time}...")
    try:
        print("Mencoba mengunduh segmen video tanpa cookies...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print("Gagal mengunduh segmen video tanpa cookies, mencoba dengan cookies:", e)
        cookie_file = get_cookie_file()
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        else:
            raise e
        
    # Check if download succeeded and get true filename
    actual_temp = temp_download
    for ext in ['.mp4', '.mkv', '.webm']:
        if os.path.exists(f"{temp_download}{ext}"):
            actual_temp = f"{temp_download}{ext}"
            break
            
    if not os.path.exists(actual_temp):
        print(f"Warning: File temp tidak ditemukan! {actual_temp}")
        pass
        
    # Buat file Subtitle (ASS) yang tersinkronisasi sempurna dari transcript_data
    sub_file_abs = None
    if with_subtitle:
        sub_file_abs = os.path.abspath(os.path.join(output_dir, f"temp_{clip_id}.ass"))
        if transcript_data:
            with open(sub_file_abs, 'w', encoding='utf-8') as sf:
                sf.write(get_ass_header())
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
                        s_str = format_ass_time(rel_s)
                        e_str = format_ass_time(rel_e)
                        clean_text = text.replace('\n', ' ').strip()
                        sf.write(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{clean_text}\n")
        else:
            # ULTIMATE FALLBACK: GEMINI AUDIO WHISPER BYPASS
            print("Transcript kosong tapi user minta Subtitle! Mengaktifkan Gemini Audio Whisper...")
            temp_audio = os.path.join(output_dir, f"temp_audio_{clip_id}.mp3")
            try:
                subprocess.run([FFMPEG_PATH, "-y", "-i", actual_temp, "-q:a", "0", "-map", "a", temp_audio], capture_output=True)
                
                def run_gemini_whisper(genai_module):
                    model = genai_module.GenerativeModel("gemini-2.5-flash")
                    print("Mengupload audio ke Gemini...")
                    audio_file = genai_module.upload_file(temp_audio)
                    try:
                        prompt = "Kamu seorang transcriber ahli. Buatkan subtitle berformat SRT murni dalam bahasa Indonesia untuk audio ini. Format waktu mulai dari 00:00:00,000. PASTIKAN SELURUH JAWABAN ANDA HANYA BERISI KODE SRT, TANPA MARKDOWN ATAU KATA PENGANTAR LAIN."
                        resp = model.generate_content([audio_file, prompt])
                        return resp.text.strip()
                    finally:
                        try: genai_module.delete_file(audio_file.name)
                        except: pass
                
                raw_srt = call_gemini_with_rotation(run_gemini_whisper)
                if raw_srt.startswith("```"):
                    raw_srt = raw_srt.split("\n", 1)[-1]
                    if raw_srt.endswith("```"): raw_srt = raw_srt[:-3]
                    raw_srt = raw_srt.replace("srt", "", 1).strip()
                    
                ass_content = srt_to_ass(raw_srt)
                with open(sub_file_abs, 'w', encoding='utf-8') as sf:
                    sf.write(ass_content)
                    
                print("Gemini Audio Whisper selesai!")
            except Exception as e:
                print("Gagal menggunakan Gemini Audio Whisper:", e)
                sub_file_abs = None
            finally:
                if os.path.exists(temp_audio):
                    try: os.remove(temp_audio)
                    except: pass

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
        
        # 3. Hardsub ala TikTok modern (Rata Tengah, Margin Bawah)
        if sub_file_abs and os.path.exists(sub_file_abs):
            print("Membakar Subtitle (Sinkronisasi Python):", sub_file_abs)
            sub_file_rel = os.path.relpath(sub_file_abs).replace('\\', '/')
            video = video.filter('subtitles', sub_file_rel)
            
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
        if sub_file_abs and os.path.exists(sub_file_abs):
            os.remove(sub_file_abs)
            
    return output_filename
