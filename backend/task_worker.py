import os
import sys
import json
import time
import html
import xml.etree.ElementTree as ET
import yt_dlp
import google.generativeai as genai
import subprocess
from dotenv import load_dotenv

# Import processor
from video_processor import create_vertical_clip

# Load environment variables
load_dotenv(override=True)

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

# Helper function to get video ID from URL
def get_video_id(url):
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    if parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed.query).get('v', [None])[0]
    return None

# Load users file
def load_users(users_file):
    if not os.path.exists(users_file):
        return []
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading users:", e)
        return []

# Save users file
def save_users(users_file, users):
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print("Error saving users:", e)
        return False

# Update task status in static/tasks/{task_id}.json
def update_task_status(task_id, status, progress, message, clips=None, original_title=None, error=None, new_credits=None, pdf_url=None):
    task_dir = os.path.join(os.path.dirname(__file__), 'static', 'tasks')
    os.makedirs(task_dir, exist_ok=True)
    task_file = os.path.join(task_dir, f"{task_id}.json")
    
    data = {
        "status": status,
        "progress": progress,
        "message": message,
        "updated_at": time.time()
    }
    if clips is not None:
        data["clips"] = clips
    if original_title is not None:
        data["original_title"] = original_title
    if error is not None:
        data["error"] = error
    if new_credits is not None:
        data["new_credits"] = new_credits
    if pdf_url is not None:
        data["pdf_url"] = pdf_url
        
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_metadata_pdf(clips, output_path):
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Helvetica", "B", 16)
        title_main = "Hasil Judul dan Deskripsi Pemotongan klip"
        pdf.cell(pdf.epw, 10, title_main.encode('latin-1', 'replace').decode('latin-1'), new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.ln(10)
        
        for i, clip in enumerate(clips):
            # Video X
            pdf.set_font("Helvetica", "B", 12)
            video_num = f"Video {i+1}"
            pdf.cell(pdf.epw, 8, video_num.encode('latin-1', 'replace').decode('latin-1'), new_x="LMARGIN", new_y="NEXT")
            
            # Judul
            pdf.set_font("Helvetica", "", 12)
            title_text = f"Judul : {clip.get('title', '')}"
            pdf.multi_cell(pdf.epw, 6, title_text.encode('latin-1', 'replace').decode('latin-1'), new_x="LMARGIN", new_y="NEXT")
            
            # Deskripsi
            desc_text = f"Deskripsi : {clip.get('viralReason', clip.get('reason', ''))}"
            pdf.multi_cell(pdf.epw, 6, desc_text.encode('latin-1', 'replace').decode('latin-1'), new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(6)
            
        pdf.output(output_path)
        print(f"[PDF] Berhasil membuat PDF di {output_path}")
        return True
    except Exception as ex:
        print("[PDF] Gagal membuat PDF:", ex)
        return False

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

def main():
    if len(sys.argv) < 8:
        print("Usage: python task_worker.py <task_id> <url> <clip_duration> <layout_mode> <username> <with_subtitle> <base_url>")
        sys.exit(1)
        
    task_id = sys.argv[1]
    url = sys.argv[2]
    clip_duration = int(sys.argv[3])
    layout_mode = sys.argv[4]
    username = sys.argv[5]
    with_subtitle = sys.argv[6].lower() == 'true'
    base_url = sys.argv[7]
    
    users_file = os.path.join(os.path.dirname(__file__), 'users.json')
    
    try:
        update_task_status(task_id, "processing", 5, "Mengekstrak informasi video...")
        
        v_id = get_video_id(url)
        if not v_id:
            raise Exception("Invalid YouTube URL")
            
        # Step 1: Extract Video Info using yt-dlp (Try without cookies first, fallback to cookies if it fails)
        ydl_opts = {'quiet': True, 'skip_download': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            print("Extract info without cookies failed, trying with cookies:", e)
            cookie_file = get_cookie_file()
            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            else:
                raise e
            
        # Step 2: Get Transcript
        update_task_status(task_id, "processing", 15, "Mengunduh transkrip/lirik video...")
        fetched_transcript_data = None
        audio_bypass_mode = False
        
        try:
            # Deteksi bahasa subtitle secara dinamis dari info youtube
            chosen_lang = None
            subtitles = info.get('subtitles') or {}
            auto_caps = info.get('automatic_captions') or {}
            
            # Prioritas: id, id-ID, en, en-US
            pref_langs = ['id', 'id-ID', 'en', 'en-US']
            for lang in pref_langs:
                if lang in subtitles or lang in auto_caps:
                    chosen_lang = lang
                    break
            
            if not chosen_lang:
                all_langs = list(subtitles.keys()) + list(auto_caps.keys())
                if all_langs:
                    chosen_lang = all_langs[0]
                    
            print(f"Subtitle language terpilih: {chosen_lang}")
            
            # Bypass youtube_transcript_api deadlock menggunakan yt-dlp native srv1 parsing (try without cookies first, fallback to cookies)
            def extract_ytdlp_transcript(vid, url_str, lang):
                if not lang:
                    return None
                outtmpl_path = os.path.join(os.path.dirname(__file__), 'static', f'tempsub_{vid}.%(ext)s')
                s_file = os.path.join(os.path.dirname(__file__), 'static', f"tempsub_{vid}.{lang}.srv1")
                
                # Coba download subtitle tanpa cookies dulu
                ops = {
                    'quiet': True, 'skip_download': True,
                    'writesubtitles': True, 'writeautomaticsub': True,
                    'subtitleslangs': [lang],
                    'subtitlesformat': 'srv1',
                    'outtmpl': outtmpl_path
                }
                print("Mencoba unduh subtitle tanpa cookies...")
                with yt_dlp.YoutubeDL(ops) as yd:
                    try:
                        yd.download([url_str])
                    except Exception as yde:
                        print("yt-dlp subtitle download without cookies failed:", yde)
                        
                # Jika gagal, coba dengan cookies
                if not os.path.exists(s_file):
                    c_file = get_cookie_file()
                    if c_file:
                        print("Subtitle tidak ditemukan, mencoba unduh dengan cookies...")
                        ops['cookiefile'] = c_file
                        with yt_dlp.YoutubeDL(ops) as yd:
                            try:
                                yd.download([url_str])
                            except Exception as yde:
                                print("yt-dlp subtitle download with cookies failed:", yde)
                                
                if not os.path.exists(s_file):
                    return None
                    
                trs = []
                try:
                    tree = ET.parse(s_file)
                    for child in tree.getroot():
                        if child.tag == 'text':
                            st = float(child.attrib.get('start', 0))
                            dr = float(child.attrib.get('dur', 0))
                            txt = child.text
                            if txt:
                                trs.append({'start': st, 'duration': dr, 'text': html.unescape(txt.replace('\n', ' ').strip())})
                except Exception as ex:
                    print("Error parsing subtitle XML:", ex)
                finally:
                    try: os.remove(s_file)
                    except: pass
                return trs
                
            fetched_transcript_data = extract_ytdlp_transcript(v_id, url, chosen_lang)
            if not fetched_transcript_data:
                raise Exception("Lirik video gagal ditarik! YouTube sedang memblokir keras IP/Wi-Fi Anda (Error 429).")
                
            full_text = " ".join([t['text'] for t in fetched_transcript_data])
            if len(full_text) > 8000:
                full_text = full_text[:8000] 
        except Exception as e:
            print("Transcript API terblokir:", e)
            full_text = ""
            fetched_transcript_data = None
            audio_bypass_mode = True
            
        # Determine target number of clips based on duration
        if clip_duration == 6:
            num_clips_target = 15
        elif clip_duration == 15:
            num_clips_target = 10
        else:
            num_clips_target = 6

        # Step 3: Analyze with Gemini AI
        base_rules = f"""
        ATURAN PENTING & MUTLAK:
        1. LEWATI (HINDARI) 3 Menit Pertama Video! (Jangan memberi klip dari detik 0-180 karena itu berisi opening/basa-basi). TAPI jika total durasi video pendek (di bawah 10 menit) atau Anda kesulitan menemukan klip yang cukup, Anda diperbolehkan mengambil dari detik 0.
        2. Cari momen EMOSIONAL TERKUAT: perdebatan panas, kemarahan, tawa meledak, kalimat hiperbola, atau pernyataan yang sangat menantang dan kontroversial.
        3. Durasi masing-masing klip HARUS masuk akal, persis {clip_duration} detik, potongan rapi, hindari kalimat yang terpotong di tengah-tengah.
        4. Balas HANYA dengan JSON valid dalam format array ini (WAJIB menghasilkan TEPAT {num_clips_target} item JSON, tidak boleh kurang):
        [
          {{
            "title": "Judul Clickbait Singkat",
            "start_time": 300,
            "end_time": {300 + clip_duration},
            "score": "99/100",
            "reason": "Sangat marah dan bernada tinggi"
          }}
        ]
        Jika Anda kesulitan menemukan momen emosional yang pas, Anda WAJIB melengkapinya dengan momen menarik atau edukatif lainnya hingga mencapai TEPAT {num_clips_target} klip. Jangan pernah mengembalikan kurang dari {num_clips_target} klip!
        """
        
        sys_prompt_text = f"Kamu adalah spesialis pemotong video TikTok. Berdasarkan teks berikut, temukan dan hasilkan TEPAT {num_clips_target} potongan (durasi {clip_duration} detik) paling EMOSIONAL, PANAS, atau HIPERBOLA.\n" + base_rules
        sys_prompt_audio = f"Kamu adalah spesialis pemotong video TikTok. DENGARKAN seluruh audio ini dan temukan serta hasilkan TEPAT {num_clips_target} potongan (durasi {clip_duration} detik) paling EMOSIONAL, PANAS, atau HIPERBOLA hanya dari mendengarkan nada suaranya!\n" + base_rules
        
        original_video_title = info.get('title', 'Video Klip')
        original_video_desc = info.get('description', '')
        if not original_video_desc:
            original_video_desc = f"Klip dari video: {original_video_title}"
            
        short_desc = original_video_desc.replace('\n', ' ').strip()
        if len(short_desc) > 200:
            short_desc = short_desc[:197] + "..."

        offline_title_templates = [
            "VIRAL! {title} - Momen Penting",
            "HOT TOPIC: {title} Terbaru",
            "EKSKLUSIF: Kupas Tuntas {title}",
            "Paling Menarik! {title} Hari Ini",
            "Bahas Tuntas: {title}",
            "Momen Penting dari {title}",
            "WAJIB TAHU! {title}",
            "Mengejutkan! Ada Apa dengan {title}?",
            "Terungkap! Rahasia di Balik {title}",
            "Fakta Menarik dari {title}",
            "Momen Emas {title}",
            "Sorotan Utama: {title}",
            "Paling Heboh! {title}",
            "Diskusi Hangat: {title}",
            "Cuplikan Terbaik: {title}"
        ]

        keys = get_gemini_keys()
        if not keys:
            print("Tidak ada API Key Gemini. Menggunakan clickbait fallback offline...")
            ai_results = []
        else:
            try:
                temp_m4a = os.path.join(os.path.dirname(__file__), 'static', f"full_audio_{v_id}.m4a")
                
                if audio_bypass_mode:
                    update_task_status(task_id, "processing", 30, "Mendeteksi pemblokiran transkrip YouTube. Mengunduh audio lengkap untuk analisis AI (1-2 menit)...")
                    import subprocess as sp
                    cmd = [sys.executable, "-m", "yt-dlp", "-f", "wa[ext=m4a]/ba[ext=m4a]/ba", "-o", temp_m4a, url]
                    print("Mengunduh audio bypass tanpa cookies...")
                    sp.run(cmd, capture_output=True)
                    
                    if not os.path.exists(temp_m4a):
                        print("Gagal mengunduh audio tanpa cookies, mencoba dengan cookies...")
                        cmd = [sys.executable, "-m", "yt-dlp", "-f", "wa[ext=m4a]/ba[ext=m4a]/ba", "-o", temp_m4a]
                        c_file = get_cookie_file()
                        if c_file:
                            cmd.extend(["--cookies", c_file])
                        cmd.append(url)
                        sp.run(cmd, capture_output=True)
                        
                    if not os.path.exists(temp_m4a):
                        raise Exception("Gagal mengunduh audio penuh untuk analisis AI.")

                def run_gemini_analysis(genai_module):
                    model = genai_module.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                    if audio_bypass_mode:
                        update_task_status(task_id, "processing", 45, "Menganalisis audio dengan Gemini AI...")
                        audio_file = genai_module.upload_file(temp_m4a)
                        try:
                            response = model.generate_content([audio_file, sys_prompt_audio])
                        finally:
                            try: genai_module.delete_file(audio_file.name)
                            except: pass
                    else:
                        update_task_status(task_id, "processing", 35, "Menganalisis transkrip dengan Gemini AI...")
                        prompt = sys_prompt_text + f"\n\nTranskrip Video:\n{full_text}"
                        response = model.generate_content(prompt)
                    return response.text.strip()

                raw_content = call_gemini_with_rotation(run_gemini_analysis)
                
                if raw_content.startswith("```json"):
                     raw_content = raw_content[7:-3]
                elif raw_content.startswith("```"):
                     raw_content = raw_content[3:-3]
                ai_results = json.loads(raw_content)
                
                if isinstance(ai_results, dict):
                    for k, v in ai_results.items():
                        if isinstance(v, list):
                            ai_results = v
                            break
                    if isinstance(ai_results, dict):
                        ai_results = [ai_results]
                
                if not isinstance(ai_results, list):
                    ai_results = []
                    
                ai_results = ai_results[:num_clips_target]
                
                # Isi jika kurang dari target
                if len(ai_results) < num_clips_target:
                    print(f"Gemini hanya menghasilkan {len(ai_results)} klip, melengkapi hingga {num_clips_target}...")
                    existing_starts = []
                    for c in ai_results:
                        if isinstance(c, dict) and 'start_time' in c:
                            try: existing_starts.append(float(c['start_time']))
                            except: pass
                                
                    total_dur = 600
                    if fetched_transcript_data:
                        try: total_dur = max(float(t['start']) + float(t['duration']) for t in fetched_transcript_data)
                        except Exception: pass
                    elif info and info.get('duration'):
                        try: total_dur = float(info.get('duration'))
                        except Exception: pass
                            
                    current_start = 180 if total_dur > 240 else 0
                    while len(ai_results) < num_clips_target and current_start + clip_duration <= total_dur:
                        overlap = False
                        for est in existing_starts:
                            if abs(current_start - est) < clip_duration:
                                overlap = True
                                break
                        if not overlap:
                            template = offline_title_templates[len(ai_results) % len(offline_title_templates)]
                            clickbait_title = template.format(title=original_video_title)
                            clickbait_desc = f"Momen menarik durasi {clip_duration} detik mengenai {short_desc}."
                            ai_results.append({
                                "title": clickbait_title,
                                "start_time": current_start,
                                "end_time": current_start + clip_duration,
                                "score": "95/100",
                                "reason": clickbait_desc
                            })
                            existing_starts.append(current_start)
                        current_start += clip_duration + 5
                        
                    while len(ai_results) < num_clips_target:
                        start_t = (len(ai_results) * (clip_duration + 2)) % max(1, int(total_dur - clip_duration))
                        template = offline_title_templates[len(ai_results) % len(offline_title_templates)]
                        clickbait_title = template.format(title=original_video_title)
                        clickbait_desc = f"Momen menarik durasi {clip_duration} detik mengenai {short_desc}."
                        ai_results.append({
                            "title": clickbait_title,
                            "start_time": start_t,
                            "end_time": start_t + clip_duration,
                            "score": "90/100",
                            "reason": clickbait_desc
                        })
                
                # Cleanup audio
                if os.path.exists(temp_m4a):
                    try: os.remove(temp_m4a)
                    except: pass
            except Exception as ai_e:
                print("Gemini API Rotation Error (Seluruh Key Habis / Gagal):", ai_e)
                ai_results = []
                
        # Alur offline clickbait templates fallback jika ai_results kosong
        if not ai_results:
            print("Mengisi data dengan offline clickbait templates...")
            total_dur = 600
            if fetched_transcript_data:
                try: total_dur = max(float(t['start']) + float(t['duration']) for t in fetched_transcript_data)
                except Exception: pass
            elif info and info.get('duration'):
                try: total_dur = float(info.get('duration'))
                except Exception: pass
                
            current_start = 180 if total_dur > 240 else 0
            for i in range(num_clips_target):
                start_t = current_start + i * (clip_duration + 5)
                if start_t + clip_duration > total_dur:
                    start_t = (i * (clip_duration + 2)) % max(1, int(total_dur - clip_duration))
                
                template = offline_title_templates[i % len(offline_title_templates)]
                clickbait_title = template.format(title=original_video_title)
                if len(clickbait_title) > 60:
                    clickbait_title = clickbait_title[:57] + "..."
                    
                clickbait_desc = f"Cuplikan menarik durasi {clip_duration} detik dari video '{original_video_title}'. Bahasan penting mengenai {short_desc}."
                ai_results.append({
                    "title": clickbait_title,
                    "start_time": start_t,
                    "end_time": start_t + clip_duration,
                    "score": f"{90 + (i % 10)}/100",
                    "reason": clickbait_desc
                })
                
        # Step 4: Cut video and generate clips
        final_clips = []
        num_clips = len(ai_results)
        
        for idx, clip in enumerate(ai_results):
            cid = f"{v_id}_{idx}"
            
            # Ensure clip duration matches requested duration
            duration = clip.get('end_time', 10) - clip.get('start_time', 0)
            if duration != clip_duration:
                clip['end_time'] = clip['start_time'] + clip_duration
                
            m = clip_duration // 60
            s = clip_duration % 60
            duration_str = f"{m:02d}:{s:02d}" if clip_duration >= 60 else f"00:{clip_duration:02d}"
            
            # Update status with current progress
            progress_val = 55 + int((idx / num_clips) * 40)
            update_task_status(task_id, "processing", progress_val, f"Memotong video klip {idx+1} dari {num_clips} (FFmpeg & Subtitles)...")
            
            try:
                static_abs_dir = os.path.join(os.path.dirname(__file__), "static")
                mp4_path = create_vertical_clip(url, clip['start_time'], clip['end_time'], output_dir=static_abs_dir, clip_id=cid, transcript_data=fetched_transcript_data, with_subtitle=with_subtitle, layout_mode=layout_mode)
                dl_url = f"{base_url}/static/{os.path.basename(mp4_path)}"
            except Exception as e:
                print("Error cutting video:", e)
                dl_url = "#"
                
            final_clips.append({
                "id": cid, 
                "title": clip.get('title') if clip.get('title') else original_video_title, 
                "duration": duration_str, 
                "score": clip.get('score', '90/100'), 
                "viralReason": clip.get('reason') if clip.get('reason') else original_video_desc, 
                "thumbnail": info.get('thumbnail', 'https://via.placeholder.com/300x500'),
                "download_url": dl_url
            })
            
        # Deduct credit if not admin
        new_credits = 0
        users = load_users(users_file)
        user_found = False
        
        for u in users:
            if u['username'].lower() == username.lower():
                user_found = True
                if u.get('role') != 'admin':
                    u['credits'] = max(0, u.get('credits', 0) - 1)
                    new_credits = u['credits']
                else:
                    new_credits = u.get('credits', 9999)
                break
                
        if user_found:
            save_users(users_file, users)
            
        # Generate PDF metadata file
        static_abs_dir = os.path.join(os.path.dirname(__file__), "static")
        pdf_filename = f"metadata_{task_id}.pdf"
        pdf_path = os.path.join(static_abs_dir, pdf_filename)
        pdf_url = None
        if generate_metadata_pdf(final_clips, pdf_path):
            pdf_url = f"{base_url}/static/{pdf_filename}"
            
        update_task_status(task_id, "completed", 100, "Selesai!", clips=final_clips, original_title=info.get('title'), new_credits=new_credits, pdf_url=pdf_url)
        print(f"Task {task_id} successfully completed!")
        
    except Exception as e:
        print("Task Worker Error:", e)
        update_task_status(task_id, "failed", 100, "Gagal", error=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
