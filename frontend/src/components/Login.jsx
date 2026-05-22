import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { User, Lock, ShieldAlert, KeyRound, Loader2, ArrowRight, Mail, Key } from 'lucide-react';
import './Login.css';

// Cookie helpers to sync fingerprints
const setCookie = (name, value, days) => {
  const date = new Date();
  date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
  const expires = "; expires=" + date.toUTCString();
  document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax; Secure";
};

const getCookie = (name) => {
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
};

// Canvas drawing fingerprinting (identifies OS text anti-aliasing + browser engine + GPU)
const getCanvasFingerprint = () => {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';
    ctx.textBaseline = "top";
    ctx.font = "14px 'Arial'";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = "#069";
    ctx.fillText("AutoClip.AI Fingerprint 1.0", 2, 15);
    ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
    ctx.fillText("AutoClip.AI Fingerprint 1.0", 4, 17);
    const dataUrl = canvas.toDataURL();
    let hash = 0;
    for (let i = 0; i < dataUrl.length; i++) {
      const char = dataUrl.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  } catch (e) {
    return '';
  }
};

// Generate highly stable web fingerprint
const getDeviceFingerprint = () => {
  let fp = localStorage.getItem('autoclip_device_fingerprint');
  if (!fp) {
    fp = getCookie('autoclip_device_fingerprint');
  }
  if (!fp) {
    const canvasHash = getCanvasFingerprint();
    const raw = [
      navigator.userAgent,
      navigator.language,
      screen.colorDepth,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      canvasHash
    ].join('|');
    
    let hash = 0;
    for (let i = 0; i < raw.length; i++) {
      const char = raw.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    fp = 'fp_' + Math.abs(hash).toString(36);
  }
  localStorage.setItem('autoclip_device_fingerprint', fp);
  setCookie('autoclip_device_fingerprint', fp, 365);
  return fp;
};

// Helper to get or create a persistent Device UUID in the browser
const getDeviceID = () => {
  let deviceId = localStorage.getItem('autoclip_device_id');
  if (!deviceId) {
    deviceId = getCookie('autoclip_device_id');
  }
  if (!deviceId) {
    deviceId = 'device_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }
  localStorage.setItem('autoclip_device_id', deviceId);
  setCookie('autoclip_device_id', deviceId, 365);
  return deviceId;
};

const Login = ({ onLoginSuccess }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [viewMode, setViewMode] = useState('login'); // 'login' | 'register' | 'verify'

  // Input states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');

  // Status states
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Dynamically set admin mode if URL has ?admin=1 query param
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('admin') === '1') {
      setIsAdmin(true);
    }
  }, []);

  const handleReset = (mode) => {
    setViewMode(mode);
    setUsername('');
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setOtpCode('');
    setError('');
    setSuccessMsg('');
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (!username || !password) return;

    setIsLoading(true);
    setError('');
    setSuccessMsg('');

    const endpoint = isAdmin 
      ? 'http://localhost:5000/api/admin/login' 
      : 'http://localhost:5000/api/login';

    axios.post(endpoint, { username, password })
      .then(res => {
        setIsLoading(false);
        onLoginSuccess(res.data.user);
      })
      .catch(err => {
        setIsLoading(false);
        if (err.response?.status === 403 && err.response?.data?.needs_verification) {
          // Transition to OTP verification
          setError('');
          setUsername(err.response.data.username);
          setViewMode('verify');
        } else {
          const errMsg = err.response?.data?.error || 'Koneksi ke server gagal.';
          setError(errMsg);
        }
      });
  };

  const handleRegisterSubmit = (e) => {
    e.preventDefault();
    if (!username || !email || !password) return;

    if (password.length < 6) {
      setError('Password minimal harus 6 karakter.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Konfirmasi password tidak cocok.');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccessMsg('');

    const deviceId = getDeviceID();
    const deviceFingerprint = getDeviceFingerprint();

    axios.post('http://localhost:5000/api/register', {
      username,
      email,
      password,
      device_id: deviceId,
      device_fingerprint: deviceFingerprint
    })
      .then(res => {
        setIsLoading(false);
        setSuccessMsg(res.data.message || 'Pendaftaran berhasil! Kode verifikasi telah dikirim ke email Anda.');
        setViewMode('verify');
      })
      .catch(err => {
        setIsLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal mendaftar.';
        setError(errMsg);
      });
  };

  const handleVerifySubmit = (e) => {
    e.preventDefault();
    if (!username || !otpCode) return;

    setIsLoading(true);
    setError('');
    setSuccessMsg('');

    axios.post('http://localhost:5000/api/verify', {
      username,
      code: otpCode
    })
      .then(res => {
        setIsLoading(false);
        setSuccessMsg('Akun berhasil diverifikasi! Mengalihkan ke dashboard...');
        
        // Auto login on success
        setTimeout(() => {
          onLoginSuccess(res.data.user);
        }, 1500);
      })
      .catch(err => {
        setIsLoading(false);
        const errMsg = err.response?.data?.error || 'Verifikasi gagal.';
        setError(errMsg);
      });
  };

  const handleResendOTP = () => {
    if (!username) return;
    setIsResending(true);
    setError('');
    setSuccessMsg('');

    axios.post('http://localhost:5000/api/resend-code', { username })
      .then(res => {
        setIsResending(false);
        setSuccessMsg(res.data.message || 'Kode verifikasi baru berhasil dikirim!');
      })
      .catch(err => {
        setIsResending(false);
        const errMsg = err.response?.data?.error || 'Gagal mengirim ulang kode.';
        setError(errMsg);
      });
  };

  return (
    <div className="login-container animate-fade-in-up">
      <div className="login-card glass-panel">
        
        {/* Card Header */}
        <div className="login-header">
          <div className={`badge ${isAdmin ? 'admin-badge' : 'creator-badge'}`}>
            {isAdmin ? <ShieldAlert size={14} /> : <KeyRound size={14} />}
            <span>
              {isAdmin 
                ? 'ADMIN PORTAL' 
                : viewMode === 'login' 
                ? 'CREATOR PORTAL' 
                : viewMode === 'register' 
                ? 'CREATOR SIGNUP' 
                : 'OTP VERIFICATION'}
            </span>
          </div>
          <h2>
            {viewMode === 'login' && (isAdmin ? 'Masuk ' : 'Mulai ')}
            {viewMode === 'register' && 'Buat '}
            {viewMode === 'verify' && 'Verifikasi '}
            <span className="gradient-text">
              {isAdmin 
                ? 'Kelola User' 
                : viewMode === 'login' 
                ? 'Buat Klip Viral' 
                : viewMode === 'register' 
                ? 'Akun Creator' 
                : 'Email Anda'}
            </span>
          </h2>
          <p className="login-subtitle">
            {isAdmin 
              ? 'Login untuk menambah atau mengelola akses Creator.' 
              : viewMode === 'login' 
              ? 'Silakan masuk menggunakan akun Creator Anda.' 
              : viewMode === 'register' 
              ? 'Daftar akun Creator baru dan dapatkan 1 kredit trial gratis.' 
              : 'Masukkan 6-digit kode OTP yang telah dikirim ke email Anda.'}
          </p>
        </div>

        {/* Message Alerts */}
        {error && (
          <div className="login-error-msg animate-shake">
            <span>⚠️ {error}</span>
          </div>
        )}
        {successMsg && (
          <div className="login-success-msg">
            <span>✅ {successMsg}</span>
          </div>
        )}

        {/* --- VIEW MODE: LOGIN --- */}
        {viewMode === 'login' && (
          <form onSubmit={handleLoginSubmit} className="login-form">
            <div className="login-input-group">
              <label htmlFor="username">Username</label>
              <div className="input-with-icon">
                <User className="input-icon" size={18} />
                <input
                  id="username"
                  type="text"
                  placeholder="Masukkan username..."
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="login-input-group">
              <label htmlFor="password">Password</label>
              <div className="input-with-icon">
                <Lock className="input-icon" size={18} />
                <input
                  id="password"
                  type="password"
                  placeholder="Masukkan password..."
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <button type="submit" className="btn-primary login-btn" disabled={isLoading}>
              {isLoading ? (
                <span className="flex-center">
                  <Loader2 className="spinner" size={18} /> Memverifikasi...
                </span>
              ) : (
                <span className="flex-center">
                  Masuk Sekarang <ArrowRight size={18} style={{ marginLeft: '6px' }} />
                </span>
              )}
            </button>
          </form>
        )}

        {/* --- VIEW MODE: REGISTER --- */}
        {viewMode === 'register' && (
          <form onSubmit={handleRegisterSubmit} className="login-form">
            <div className="login-input-group">
              <label htmlFor="reg-username">Username</label>
              <div className="input-with-icon">
                <User className="input-icon" size={18} />
                <input
                  id="reg-username"
                  type="text"
                  placeholder="Pilih username unik..."
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="login-input-group">
              <label htmlFor="reg-email">Alamat Email</label>
              <div className="input-with-icon">
                <Mail className="input-icon" size={18} />
                <input
                  id="reg-email"
                  type="email"
                  placeholder="Masukkan email untuk verifikasi..."
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="login-input-group">
              <label htmlFor="reg-password">Password</label>
              <div className="input-with-icon">
                <Lock className="input-icon" size={18} />
                <input
                  id="reg-password"
                  type="password"
                  placeholder="Minimal 6 karakter..."
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="login-input-group">
              <label htmlFor="reg-confirm">Konfirmasi Password</label>
              <div className="input-with-icon">
                <Lock className="input-icon" size={18} />
                <input
                  id="reg-confirm"
                  type="password"
                  placeholder="Ketik ulang password..."
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <button type="submit" className="btn-primary login-btn" disabled={isLoading}>
              {isLoading ? (
                <span className="flex-center">
                  <Loader2 className="spinner" size={18} /> Mendaftarkan...
                </span>
              ) : (
                <span className="flex-center">
                  Daftar Akun Baru <ArrowRight size={18} style={{ marginLeft: '6px' }} />
                </span>
              )}
            </button>
          </form>
        )}

        {/* --- VIEW MODE: VERIFY --- */}
        {viewMode === 'verify' && (
          <form onSubmit={handleVerifySubmit} className="login-form">
            <div className="login-input-group">
              <label>Username</label>
              <div className="input-with-icon">
                <User className="input-icon" size={18} />
                <input
                  type="text"
                  value={username}
                  disabled
                  style={{ opacity: 0.7, background: 'rgba(255,255,255,0.01)' }}
                />
              </div>
            </div>

            <div className="login-input-group">
              <label htmlFor="otp-code">Kode Verifikasi (OTP)</label>
              <div className="input-with-icon">
                <Key className="input-icon" size={18} />
                <input
                  id="otp-code"
                  type="text"
                  placeholder="Masukkan 6 digit kode..."
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.trim())}
                  maxLength={6}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="otp-resend-container">
              <span>Tidak menerima kode?</span>
              <button 
                type="button" 
                className="resend-btn" 
                onClick={handleResendOTP} 
                disabled={isResending || isLoading}
              >
                {isResending ? 'Mengirim...' : 'Kirim Ulang'}
              </button>
            </div>

            <button type="submit" className="btn-primary login-btn" disabled={isLoading}>
              {isLoading ? (
                <span className="flex-center">
                  <Loader2 className="spinner" size={18} /> Mengaktifkan...
                </span>
              ) : (
                <span className="flex-center">
                  Verifikasi Akun <ArrowRight size={18} style={{ marginLeft: '6px' }} />
                </span>
              )}
            </button>
          </form>
        )}

        {/* Footer Navigation */}
        <div className="login-footer">
          {isAdmin ? (
            <span className="footer-text">
              Portal Pengelolaan Khusus Admin.
            </span>
          ) : viewMode === 'login' ? (
            <span className="footer-text">
              Belum punya akun?
              <button onClick={() => handleReset('register')} className="toggle-mode-btn">
                Buat Akun
              </button>
            </span>
          ) : viewMode === 'register' ? (
            <span className="footer-text">
              Sudah punya akun?
              <button onClick={() => handleReset('login')} className="toggle-mode-btn">
                Masuk
              </button>
            </span>
          ) : (
            <span className="footer-text">
              Kembali ke
              <button onClick={() => handleReset('login')} className="toggle-mode-btn">
                Portal Login
              </button>
            </span>
          )}
        </div>

      </div>
    </div>
  );
};

export default Login;
