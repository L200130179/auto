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
def update_task_status(task_id, status, progress, message, clips=None, original_title=None, error=None, new_credits=None):
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
        
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

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
            
        # Step 1: Extract Video Info using yt-dlp
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        # Step 2: Get Transcript
        update_task_status(task_id, "processing", 15, "Mengunduh transkrip/lirik video...")
        fetched_transcript_data = None
        audio_bypass_mode = False
        
        try:
            # Bypass youtube_transcript_api deadlock menggunakan yt-dlp native srv1 parsing
            def extract_ytdlp_transcript(vid, url_str):
                ops = {
                    'quiet': True, 'skip_download': True,
                    'writesubtitles': True, 'writeautomaticsub': True,
                    'subtitleslangs': ['id', 'en', 'en-US'],
                    'subtitlesformat': 'srv1',
                    'outtmpl': f'static/tempsub_{vid}.%(ext)s'
                }
                with yt_dlp.YoutubeDL(ops) as yd:
                    yd.download([url_str])
                    
                s_file = None
                for lng in ['id', 'en', 'en-US']:
                    pth = f"static/tempsub_{vid}.{lng}.srv1"
                    if os.path.exists(pth):
                        s_file = pth
                        break
                if not s_file:
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
                finally:
                    try: os.remove(s_file)
                    except: pass
                return trs
                
            fetched_transcript_data = extract_ytdlp_transcript(v_id, url)
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
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key or gemini_key == "YOUR_GEMINI_API_KEY":
            ai_results = []
            for i in range(num_clips_target):
                start = 180 + i * (clip_duration + 5)
                ai_results.append({
                    "title": f"Klip Mock {i+1} (API Key Belum Diset)",
                    "start_time": start,
                    "end_time": start + clip_duration,
                    "score": "95/100",
                    "reason": "Mohon isi .env"
                })
        else:
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                
                audio_file = None
                temp_m4a = f"static/full_audio_{v_id}.m4a"
                
                if audio_bypass_mode:
                    update_task_status(task_id, "processing", 30, "Mendeteksi pemblokiran transkrip YouTube. Mengunduh audio lengkap untuk analisis AI (1-2 menit)...")
                    import subprocess as sp
                    sp.run([sys.executable, "-m", "yt-dlp", "-f", "wa[ext=m4a]/ba[ext=m4a]/ba", "-o", temp_m4a, url], capture_output=True)
                    
                    if os.path.exists(temp_m4a):
                        update_task_status(task_id, "processing", 45, "Menganalisis audio dengan Gemini AI...")
                        audio_file = genai.upload_file(temp_m4a)
                        response = model.generate_content([audio_file, sys_prompt_audio])
                    else:
                        raise Exception("Gagal mengunduh audio penuh untuk analisis AI.")
                else:
                    update_task_status(task_id, "processing", 35, "Menganalisis transkrip dengan Gemini AI...")
                    prompt = sys_prompt_text + f"\n\nTranskrip Video:\n{full_text}"
                    response = model.generate_content(prompt)
                
                raw_content = response.text.strip()
                if raw_content.startswith("```json"):
                     raw_content = raw_content[7:-3]
                elif raw_content.startswith("```"):
                     raw_content = raw_content[3:-3]
                ai_results = json.loads(raw_content)
                
                if isinstance(ai_results, dict):
                    # Jika berupa dict dengan list di dalamnya, ekstrak list tersebut
                    for k, v in ai_results.items():
                        if isinstance(v, list):
                            ai_results = v
                            break
                    if isinstance(ai_results, dict):
                        ai_results = [ai_results]
                
                if not isinstance(ai_results, list):
                    ai_results = []
                    
                # Trim jika terlalu banyak
                ai_results = ai_results[:num_clips_target]
                
                # Isi jika kurang dari target
                if len(ai_results) < num_clips_target:
                    print(f"Gemini returned only {len(ai_results)} clips, filling up to {num_clips_target}...")
                    existing_starts = []
                    for c in ai_results:
                        if isinstance(c, dict) and 'start_time' in c:
                            try:
                                existing_starts.append(float(c['start_time']))
                            except:
                                pass
                                
                    total_dur = 600
                    if fetched_transcript_data:
                        try:
                            total_dur = max(float(t['start']) + float(t['duration']) for t in fetched_transcript_data)
                        except Exception:
                            pass
                    elif info and info.get('duration'):
                        try:
                            total_dur = float(info.get('duration'))
                        except Exception:
                            pass
                            
                    current_start = 180 if total_dur > 240 else 0
                    while len(ai_results) < num_clips_target and current_start + clip_duration <= total_dur:
                        overlap = False
                        for est in existing_starts:
                            if abs(current_start - est) < clip_duration:
                                overlap = True
                                break
                        if not overlap:
                            ai_results.append({
                                "title": f"Momen Menarik Tambahan {len(ai_results) + 1}",
                                "start_time": current_start,
                                "end_time": current_start + clip_duration,
                                "score": "95/100",
                                "reason": "Analisis auto-segmentasi"
                            })
                            existing_starts.append(current_start)
                        current_start += clip_duration + 5
                        
                    while len(ai_results) < num_clips_target:
                        start_t = (len(ai_results) * (clip_duration + 2)) % max(1, int(total_dur - clip_duration))
                        ai_results.append({
                            "title": f"Momen Menarik Cadangan {len(ai_results) + 1}",
                            "start_time": start_t,
                            "end_time": start_t + clip_duration,
                            "score": "90/100",
                            "reason": "Segmentasi cadangan"
                        })
                
                # Cleanup audio
                if audio_file:
                    try:
                        genai.delete_file(audio_file.name)
                        if os.path.exists(temp_m4a): os.remove(temp_m4a)
                    except: pass
            except Exception as ai_e:
                print("Gemini API Error:", ai_e)
                ai_results = []
                for i in range(num_clips_target):
                    start = 180 + i * (clip_duration + 5)
                    ai_results.append({
                        "title": f"Momen Menarik {i+1}",
                        "start_time": start,
                        "end_time": start + clip_duration,
                        "score": "99/100",
                        "reason": "Mode Darurat Aktif"
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
                # If API key is set, cut video for real
                if gemini_key and gemini_key != "YOUR_GEMINI_API_KEY":
                    mp4_path = create_vertical_clip(url, clip['start_time'], clip['end_time'], output_dir="static", clip_id=cid, transcript_data=fetched_transcript_data, with_subtitle=with_subtitle, layout_mode=layout_mode)
                    dl_url = f"{base_url}/{mp4_path.replace(os.sep, '/')}"
                else:
                    dl_url = "#"
            except Exception as e:
                print("Error cutting video:", e)
                dl_url = "#"
                
            final_clips.append({
                "id": cid, 
                "title": clip.get('title', 'Video Klip'), 
                "duration": duration_str, 
                "score": clip.get('score', '90/100'), 
                "viralReason": clip.get('reason', 'Hook Menarik'), 
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
            
        update_task_status(task_id, "completed", 100, "Selesai!", clips=final_clips, original_title=info.get('title'), new_credits=new_credits)
        print(f"Task {task_id} successfully completed!")
        
    except Exception as e:
        print("Task Worker Error:", e)
        update_task_status(task_id, "failed", 100, "Gagal", error=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
