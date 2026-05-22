from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import json
import time
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# Custom processor
from video_processor import create_vertical_clip

load_dotenv(override=True)
app = Flask(__name__)
CORS(app)

# BASE_URL untuk link download video hasil clip.
# Bisa diset via .env: BASE_URL=https://domainanda.com
# Jika tidak diset, akan otomatis menggunakan Host header dari request (bekerja di balik Nginx)
BASE_URL_ENV = os.environ.get('BASE_URL', '').rstrip('/')


USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_settings():
    default_settings = {
        "topup_instruction": "Topup silahkan kirim sesuai harga token kredit 1 kredit = Rp. 2.000,00 . kirim melalui DANA 082221327047 dan konfirmasi juga pembayaran ke nomor WA tersebut. Terima kasih.",
        "auto_cleanup": True
    }
    if not os.path.exists(SETTINGS_FILE):
        return default_settings
    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in default_settings.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print("Error loading settings:", e)
        return default_settings

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print("Error saving settings:", e)
        return False

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading users:", e)
        return []

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print("Error saving users:", e)
        return False

# Helper to detect MAC address of client machine
def get_client_mac(ip):
    import uuid
    import subprocess
    import re
    if ip in ['127.0.0.1', 'localhost', '::1']:
        try:
            # Localhost MAC
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
            return mac
        except Exception:
            return None
    try:
        # Run arp -a <ip>
        output = subprocess.check_output(f"arp -a {ip}", shell=True).decode('utf-8')
        match = re.search(r'([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})', output)
        if match:
            return match.group(0).replace('-', ':').lower()
    except Exception as e:
        print("Error getting MAC from ARP:", e)
    return None

# Helper to send email or fallback to log file
def send_verification_email(email, code):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_server = os.environ.get('SMTP_SERVER', '')
    smtp_port_str = os.environ.get('SMTP_PORT', '587')
    smtp_user = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_from = os.environ.get('SMTP_FROM', 'noreply@autoclip.ai')
    
    if not smtp_server or not smtp_user or not smtp_password:
        print(f"SMTP not configured. Verification code for {email} is: {code}")
        try:
            log_path = os.path.join(os.path.dirname(__file__), 'verification_emails.log')
            with open(log_path, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Code for {email}: {code}\n")
        except Exception as e:
            print("Failed to write verification log:", e)
        return True
        
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 587
        
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = email
        msg['Subject'] = 'AutoClip.AI - Verifikasi Akun Baru'
        
        # Premium dark-mode HTML Template
        html_body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b0c10; color: #c5c6c7; padding: 30px; margin: 0;">
            <div style="max-width: 500px; margin: 20px auto; background: linear-gradient(145deg, #151c24, #0f141a); padding: 40px; border-radius: 16px; border: 1px solid rgba(0, 229, 255, 0.2); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); text-align: center;">
                <h2 style="color: #ffffff; margin-bottom: 8px; font-weight: 800; font-size: 24px; letter-spacing: -0.5px;">AutoClip<span style="color: #00e5ff;">.AI</span></h2>
                <div style="font-size: 11px; font-weight: 700; color: #00e5ff; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 24px;">CREATOR VERIFICATION</div>
                <p style="font-size: 15px; line-height: 1.6; color: #e2e8f0; margin-bottom: 24px; text-align: left;">Halo Creator,</p>
                <p style="font-size: 15px; line-height: 1.6; color: #94a3b8; text-align: left; margin-bottom: 24px;">Terima kasih telah mendaftar di AutoClip.AI. Gunakan kode verifikasi di bawah ini untuk mengaktifkan akun Anda dan mengklaim <strong>1 kredit trial gratis</strong>:</p>
                <div style="background: rgba(0, 229, 255, 0.08); border: 1px dashed #00e5ff; padding: 18px 24px; border-radius: 12px; font-size: 32px; font-weight: 800; letter-spacing: 5px; color: #00e5ff; margin: 28px 0; text-shadow: 0 0 15px rgba(0, 229, 255, 0.3);">
                    {code}
                </div>
                <p style="font-size: 12px; color: #64748b; margin-top: 32px; text-align: left;">Kode ini berlaku untuk sesi registrasi saat ini. Demi keamanan akun Anda, jangan sebarkan kode ini kepada pihak lain.</p>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 24px 0;">
                <p style="font-size: 10px; color: #475569;">&copy; {time.strftime('%Y')} AutoClip.AI. Hak Cipta Dilindungi.</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=12)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_from, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email via SMTP:", e)
        try:
            log_path = os.path.join(os.path.dirname(__file__), 'verification_emails.log')
            with open(log_path, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] FAILED SMTP SEND to {email}. Code: {code}. Error: {e}\n")
        except Exception:
            pass
        return False

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username dan password wajib diisi"}), 400
        
    users = load_users()
    for user in users:
        if user['username'].lower() == username.lower() and user['password'] == password:
            # Check verified status for creator
            if user.get('role', 'creator') != 'admin' and user.get('is_verified') == False:
                return jsonify({
                    "error": "Akun Anda belum terverifikasi. Silakan lakukan verifikasi email.",
                    "needs_verification": True,
                    "username": user['username']
                }), 403

            return jsonify({
                "message": "Login berhasil",
                "user": {
                    "username": user['username'],
                    "role": user.get('role', 'creator'),
                    "credits": user.get('credits', 10)
                }
            })
            
    return jsonify({"error": "Username atau password salah"}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    device_id = data.get('device_id', '').strip()
    device_fingerprint = data.get('device_fingerprint', '').strip()
    
    if not username or not email or not password:
        return jsonify({"error": "Semua field (Username, Email, Password) wajib diisi"}), 400
        
    if len(username) < 3:
        return jsonify({"error": "Username minimal harus 3 karakter"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password minimal harus 6 karakter"}), 400
    if '@' not in email or '.' not in email:
        return jsonify({"error": "Format email tidak valid"}), 400
        
    users = load_users()
    for u in users:
        if u['username'].lower() == username.lower():
            return jsonify({"error": "Username sudah terdaftar"}), 400
        if u.get('email', '').lower() == email.lower():
            return jsonify({"error": "Email sudah terdaftar"}), 400
            
    # Anti-cheating check: IP, Client device fingerprint, device ID, and LAN MAC (fallback)
    client_ip = request.remote_addr
    client_mac = get_client_mac(client_ip)
    
    for u in users:
        if u.get('role', 'creator') == 'admin':
            continue
        # Only block duplicates from fully verified users to avoid trapping failures
        if u.get('is_verified', True):
            if device_id and u.get('device_id') == device_id:
                return jsonify({"error": "Pendaftaran ditolak: Perangkat Anda telah digunakan untuk mendaftar akun trial."}), 400
            if device_fingerprint and u.get('device_fingerprint') == device_fingerprint:
                return jsonify({"error": "Pendaftaran ditolak: Perangkat Anda telah terdeteksi mendaftar akun trial sebelumnya."}), 400
            if client_mac and u.get('mac_address') and u.get('mac_address') == client_mac:
                return jsonify({"error": "Pendaftaran ditolak: Alamat perangkat (MAC) Anda telah digunakan untuk mendaftar akun trial."}), 400

    # Generate code
    import random
    verification_code = str(random.randint(100000, 999999))
    
    new_user = {
        "username": username,
        "email": email,
        "password": password,
        "role": "creator",
        "credits": 1, # Trial credit
        "is_verified": False,
        "verification_code": verification_code,
        "device_id": device_id,
        "device_fingerprint": device_fingerprint,
        "ip_address": client_ip,
        "mac_address": client_mac or '',
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if not send_verification_email(email, verification_code):
        return jsonify({"error": "Gagal mengirimkan email verifikasi. Pastikan email Anda benar."}), 500
        
    users.append(new_user)
    if save_users(users):
        return jsonify({"message": "Pendaftaran berhasil. Silakan cek email Anda untuk kode verifikasi."})
    else:
        return jsonify({"error": "Gagal menyimpan data pengguna"}), 500

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.json or {}
    username = data.get('username', '').strip()
    code = data.get('code', '').strip()
    
    if not username or not code:
        return jsonify({"error": "Username dan kode verifikasi wajib diisi"}), 400
        
    users = load_users()
    found_user = None
    for u in users:
        if u['username'].lower() == username.lower():
            found_user = u
            break
            
    if not found_user:
        return jsonify({"error": "User tidak ditemukan"}), 404
        
    if found_user.get('is_verified', False):
        return jsonify({"error": "Akun ini sudah terverifikasi sebelumnya"}), 400
        
    if found_user.get('verification_code') != code:
        return jsonify({"error": "Kode verifikasi salah atau tidak cocok"}), 400
        
    found_user['is_verified'] = True
    if 'verification_code' in found_user:
        del found_user['verification_code']
        
    if save_users(users):
        return jsonify({
            "message": "Akun berhasil diverifikasi",
            "user": {
                "username": found_user['username'],
                "role": found_user.get('role', 'creator'),
                "credits": found_user.get('credits', 1)
            }
        })
    else:
        return jsonify({"error": "Gagal mengaktifkan akun"}), 500

@app.route('/api/resend-code', methods=['POST'])
def api_resend_code():
    data = request.json or {}
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({"error": "Username wajib diisi"}), 400
        
    users = load_users()
    found_user = None
    for u in users:
        if u['username'].lower() == username.lower():
            found_user = u
            break
            
    if not found_user:
        return jsonify({"error": "User tidak ditemukan"}), 404
        
    if found_user.get('is_verified', False):
        return jsonify({"error": "Akun ini sudah terverifikasi"}), 400
        
    import random
    verification_code = str(random.randint(100000, 999999))
    found_user['verification_code'] = verification_code
    
    if not send_verification_email(found_user['email'], verification_code):
        return jsonify({"error": "Gagal mengirimkan kode baru."}), 500
        
    if save_users(users):
        return jsonify({"message": "Kode verifikasi baru berhasil dikirim!"})
    else:
        return jsonify({"error": "Gagal memperbarui kode verifikasi"}), 500



@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username dan password wajib diisi"}), 400
        
    users = load_users()
    for user in users:
        if user['username'].lower() == username.lower() and user['password'] == password and user.get('role') == 'admin':
            return jsonify({
                "message": "Login Admin berhasil",
                "user": {
                    "username": user['username'],
                    "role": 'admin',
                    "credits": user.get('credits', 9999)
                }
            })
            
    return jsonify({"error": "Username/password salah atau Anda bukan Admin"}), 401

@app.route('/api/admin/users', methods=['GET'])
def api_get_users():
    users = load_users()
    sanitized = []
    for u in users:
        sanitized.append({
            "username": u['username'],
            "email": u.get('email', ''),
            "password": u.get('password', ''),
            "role": u.get('role', 'creator'),
            "credits": u.get('credits', 10),
            "created_at": u.get('created_at', '')
        })
    return jsonify({"users": sanitized})

@app.route('/api/admin/users', methods=['POST'])
def api_add_user():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip() or f"{username.lower()}@autoclip.ai"
    password = data.get('password', '').strip()
    role = data.get('role', 'creator').strip()
    credits_val = data.get('credits', 10)
    
    try:
        credits_val = int(credits_val)
    except (ValueError, TypeError):
        credits_val = 10
        
    if not username or not password:
        return jsonify({"error": "Username dan password wajib diisi"}), 400
        
    users = load_users()
    for user in users:
        if user['username'].lower() == username.lower():
            return jsonify({"error": "Username sudah terdaftar"}), 400
            
    new_user = {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
        "credits": credits_val,
        "is_verified": True, # Admin created users are verified by default
        "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    users.append(new_user)
    if save_users(users):
        return jsonify({"message": "User berhasil ditambahkan", "user": {
            "username": username,
            "role": role,
            "credits": credits_val,
            "created_at": new_user['created_at']
        }})
    else:
        return jsonify({"error": "Gagal menyimpan user"}), 500

@app.route('/api/admin/users/update-credit', methods=['POST'])
def api_update_credit():
    data = request.json or {}
    username = data.get('username', '').strip()
    credits_val = data.get('credits')
    
    if not username or credits_val is None:
        return jsonify({"error": "Username dan credits wajib diisi"}), 400
        
    try:
        credits_val = int(credits_val)
    except ValueError:
        return jsonify({"error": "Credits harus berupa angka"}), 400
        
    users = load_users()
    found = False
    for user in users:
        if user['username'].lower() == username.lower():
            user['credits'] = credits_val
            found = True
            break
            
    if not found:
        return jsonify({"error": "User tidak ditemukan"}), 404
        
    if save_users(users):
        return jsonify({"message": f"Kredit untuk {username} berhasil diperbarui menjadi {credits_val}", "credits": credits_val})
    else:
        return jsonify({"error": "Gagal menyimpan kredit"}), 500

@app.route('/api/admin/users', methods=['DELETE'])
def api_delete_user():
    data = request.json or {}
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({"error": "Username wajib diisi"}), 400
        
    users = load_users()
    # Filter out target user
    updated_users = [u for u in users if u['username'].lower() != username.lower()]
    
    if len(updated_users) == len(users):
        return jsonify({"error": "User tidak ditemukan"}), 404
        
    if save_users(updated_users):
        return jsonify({"message": f"User '{username}' berhasil dihapus."})
    else:
        return jsonify({"error": "Gagal menghapus user dari sistem"}), 500

@app.route('/api/admin/users/update', methods=['POST'])
def api_admin_update_user():
    data = request.json or {}
    username = data.get('username', '').strip()
    new_username = data.get('new_username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', '').strip()
    credits_val = data.get('credits')
    
    if not username:
        return jsonify({"error": "Username asal wajib diisi"}), 400
        
    users = load_users()
    target_user = None
    for u in users:
        if u['username'].lower() == username.lower():
            target_user = u
            break
            
    if not target_user:
        return jsonify({"error": "User tidak ditemukan"}), 404
        
    # Check duplicate username if renaming
    if new_username and new_username.lower() != username.lower():
        for u in users:
            if u['username'].lower() == new_username.lower():
                return jsonify({"error": "Username baru sudah terdaftar"}), 400
        target_user['username'] = new_username
        
    if email:
        target_user['email'] = email
        
    if password:
        target_user['password'] = password
        
    if role:
        target_user['role'] = role
        
    if credits_val is not None:
        try:
            target_user['credits'] = int(credits_val)
        except ValueError:
            return jsonify({"error": "Kredit harus berupa angka"}), 400
            
    if save_users(users):
        return jsonify({"message": f"User '{username}' berhasil diperbarui."})
    else:
        return jsonify({"error": "Gagal menyimpan perubahan user"}), 500

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    settings = load_settings()
    return jsonify(settings)

@app.route('/api/admin/settings', methods=['POST'])
def api_update_settings():
    data = request.json or {}
    instruction = data.get('topup_instruction', '').strip()
    
    if not instruction:
        return jsonify({"error": "Petunjuk topup tidak boleh kosong"}), 400
        
    settings = load_settings()
    settings['topup_instruction'] = instruction
    
    if save_settings(settings):
        return jsonify({"message": "Pengaturan berhasil disimpan", "settings": settings})
    else:
        return jsonify({"error": "Gagal menyimpan pengaturan"}), 500

@app.route('/api/admin/gemini-key', methods=['GET'])
def api_get_gemini_key():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    key_val = ""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    key_val = line.strip().split("GEMINI_API_KEY=", 1)[1]
                    break
    if not key_val:
        key_val = os.environ.get("GEMINI_API_KEY", "")
    return jsonify({"gemini_key": key_val})

@app.route('/api/admin/gemini-key', methods=['POST'])
def api_update_gemini_key():
    data = request.json or {}
    new_key = data.get('gemini_key', '').strip()
    
    if not new_key:
        return jsonify({"error": "Gemini API Key tidak boleh kosong"}), 400
        
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    lines = []
    found = False
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            
    # Search for variable to replace
    for i, line in enumerate(lines):
        if line.strip().startswith("GEMINI_API_KEY="):
            lines[i] = f"GEMINI_API_KEY={new_key}\n"
            found = True
            break
            
    if not found:
        if lines and not lines[-1].endswith('\n'):
            lines[-1] = lines[-1] + '\n'
        lines.append(f"GEMINI_API_KEY={new_key}\n")
        
    try:
        with open(env_path, 'w') as f:
            f.writelines(lines)
        # Update current environment variable dynamically
        os.environ["GEMINI_API_KEY"] = new_key
        return jsonify({"message": "GEMINI_API_KEY berhasil diperbarui!"})
    except Exception as e:
        print("Error saving GEMINI_API_KEY:", e)
        return jsonify({"error": "Gagal menyimpan GEMINI_API_KEY ke berkas .env"}), 500

@app.route('/api/admin/clean-static', methods=['POST'])
def api_clean_static():
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        return jsonify({"message": "Folder static tidak ditemukan."}), 200
        
    count = 0
    errors = []
    extensions = ('.mp4', '.m4a', '.mp3', '.vtt', '.srv1', '.json3')
    for filename in os.listdir(static_dir):
        file_path = os.path.join(static_dir, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(extensions):
            try:
                os.remove(file_path)
                count += 1
            except Exception as e:
                errors.append(f"Gagal menghapus {filename}: {str(e)}")
                
    if errors:
        return jsonify({"error": f"Dibersihkan {count} berkas, tetapi ada {len(errors)} berkas gagal dihapus.", "details": errors}), 207
        
    return jsonify({"message": f"Berhasil membersihkan {count} berkas media dari folder static."})

@app.route('/api/admin/toggle-cleanup', methods=['POST'])
def api_toggle_cleanup():
    data = request.json or {}
    enabled = data.get('auto_cleanup', True)
    
    settings = load_settings()
    settings['auto_cleanup'] = bool(enabled)
    
    if save_settings(settings):
        return jsonify({
            "message": f"Auto-cleanup berhasil {'diaktifkan' if enabled else 'dinonaktifkan'}.",
            "auto_cleanup": settings['auto_cleanup']
        })
    else:
        return jsonify({"error": "Gagal menyimpan pengaturan auto-cleanup"}), 500



def get_video_id(url):
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    if parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed.query).get('v', [None])[0]
    return None

@app.route('/api/process', methods=['POST'])
def process_video():
    data = request.json
    url = data.get('url')
    with_subtitle = data.get('with_subtitle', True)
    clip_duration = int(data.get('clip_duration', 30))
    layout_mode = data.get('layout_mode', 'auto_magic')
    username = data.get('username')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    if not username:
        return jsonify({"error": "Username wajib dikirim untuk memproses video"}), 400
        
    v_id = get_video_id(url)
    if not v_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
        
    users = load_users()
    user_obj = None
    for u in users:
        if u['username'].lower() == username.lower():
            user_obj = u
            break
            
    if not user_obj:
        return jsonify({"error": "User tidak ditemukan"}), 404
        
    is_admin = user_obj.get('role') == 'admin'
    user_credits = user_obj.get('credits', 0)
    
    if not is_admin and user_credits <= 0:
        return jsonify({"error": "Kredit Anda habis! Silakan hubungi Admin untuk menambah kredit."}), 403
        
    try:
        # Generate unique task ID
        import uuid
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Initialize task status file
        task_dir = os.path.join(os.path.dirname(__file__), 'static', 'tasks')
        os.makedirs(task_dir, exist_ok=True)
        task_file = os.path.join(task_dir, f"{task_id}.json")
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "pending",
                "progress": 0,
                "message": "Mengantri di server..."
            }, f, indent=2)
            
        # Determine base URL for download links
        if BASE_URL_ENV:
            base_url = BASE_URL_ENV
        else:
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
            host = request.headers.get('X-Forwarded-Host', request.host)
            base_url = f"{scheme}://{host}"
            
        # Trigger background worker process
        import sys
        import subprocess
        python_bin = sys.executable
        subprocess.Popen([
            python_bin,
            'task_worker.py',
            task_id,
            url,
            str(clip_duration),
            layout_mode,
            username,
            str(with_subtitle),
            base_url
        ])
        
        return jsonify({"task_id": task_id}), 202
        
    except Exception as e:
        print("Backend Process Error:", repr(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task_dir = os.path.join(os.path.dirname(__file__), 'static', 'tasks')
    task_file = os.path.join(task_dir, f"{task_id}.json")
    
    if not os.path.exists(task_file):
        return jsonify({"error": "Task tidak ditemukan"}), 404
        
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Gagal membaca status task: {str(e)}"}), 500

if __name__ == '__main__':
    # Start auto-cleanup thread for static folder (expires files > 1 hour old)
    def start_cleanup_thread():
        import threading
        def cleanup_loop():
            time.sleep(10)
            print("[Cleanup] Auto-cleanup thread active.")
            while True:
                try:
                    settings = load_settings()
                    if settings.get('auto_cleanup', True):
                        static_dir = os.path.join(os.path.dirname(__file__), 'static')
                        if os.path.exists(static_dir):
                            now = time.time()
                            # Clean files in static/
                            extensions = ('.mp4', '.m4a', '.mp3', '.vtt', '.srv1', '.json3')
                            for filename in os.listdir(static_dir):
                                file_path = os.path.join(static_dir, filename)
                                if os.path.isfile(file_path) and filename.lower().endswith(extensions):
                                    file_time = os.path.getmtime(file_path)
                                    # 1 hour = 3600 seconds
                                    if now - file_time > 3600:
                                        try:
                                            os.remove(file_path)
                                            print(f"[Cleanup] Automatically deleted expired file: {filename}")
                                        except Exception as e:
                                            print(f"[Cleanup] Failed to delete {filename}: {e}")
                            
                            # Clean files in static/tasks/
                            tasks_dir = os.path.join(static_dir, 'tasks')
                            if os.path.exists(tasks_dir):
                                for filename in os.listdir(tasks_dir):
                                    file_path = os.path.join(tasks_dir, filename)
                                    if os.path.isfile(file_path) and filename.lower().endswith('.json'):
                                        file_time = os.path.getmtime(file_path)
                                        # 2 hours = 7200 seconds
                                        if now - file_time > 7200:
                                            try:
                                                os.remove(file_path)
                                                print(f"[Cleanup] Automatically deleted expired task file: {filename}")
                                            except Exception as e:
                                                print(f"[Cleanup] Failed to delete task file {filename}: {e}")
                except Exception as e:
                    print(f"[Cleanup] Error in loop: {e}")
                # Check every 10 minutes (600 seconds)
                time.sleep(600)

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_cleanup_thread()

    app.run(port=5000, debug=True)
