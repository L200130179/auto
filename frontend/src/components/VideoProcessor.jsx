import React, { useState } from 'react';
import axios from 'axios';
import { Film, Wand2, Loader2, Play, Download } from 'lucide-react';
import './VideoProcessor.css';
import './VideoProcessor.css';

const MOCK_CLIPS = [
  { id: 1, title: "Cara AI Mengubah Industri Tech", duration: "00:45", score: "98/100", viralReason: "Hook kuat di awal, emosional", thumbnail: "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=300&h=500" },
  { id: 2, title: "Kenapa Anda Harus Belajar Coding Sekarang", duration: "00:59", score: "92/100", viralReason: "Topik sangat relevan, call to action jelas", thumbnail: "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=300&h=500" },
  { id: 3, title: "Framework JS Terbaik 2026", duration: "00:30", score: "88/100", viralReason: "Kontroversial dan memicu diskusi", thumbnail: "https://images.unsplash.com/photo-1633356122544-f134324a6cee?auto=format&fit=crop&q=80&w=300&h=500" }
];

const VideoProcessor = ({ user, onUpdateCredits }) => {
  const [url, setUrl] = useState('');
  const [withSubtitle, setWithSubtitle] = useState(true);
  const [clipDuration, setClipDuration] = useState(30);
  const [layoutMode, setLayoutMode] = useState('auto_magic');
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [clips, setClips] = useState(null);
  const progressIntervalRef = React.useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url) return;
    
    setIsProcessing(true);
    setLoadingProgress(0);
    setClips(null);

    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    progressIntervalRef.current = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 99) {
          clearInterval(progressIntervalRef.current);
          return 99;
        }
        const increment = prev < 40 ? Math.random() * 6 : prev < 75 ? Math.random() * 3 : Math.random() * 0.5;
        return Math.min(99, prev + increment);
      });
    }, 600);

    // Simulate API call using our actual Flask backend
    axios.post('http://localhost:5000/api/process', { 
      url, 
      with_subtitle: withSubtitle, 
      clip_duration: clipDuration, 
      layout_mode: layoutMode,
      username: user?.username 
    })
      .then(res => {
        clearInterval(progressIntervalRef.current);
        setLoadingProgress(100);
        
        if (res.data.new_credits !== undefined) {
          onUpdateCredits(res.data.new_credits);
        }
        
        setTimeout(() => {
          setClips(res.data.clips);
          setIsProcessing(false);
          setLoadingProgress(0);
        }, 500);
      })
      .catch(err => {
        console.error(err);
        clearInterval(progressIntervalRef.current);
        setIsProcessing(false);
        setLoadingProgress(0);
        const serverError = err.response?.data?.error || 'Terjadi kesalahan saat memproses video.';
        alert(serverError);
      });
  };

  const hasNoCredits = user?.role !== 'admin' && (user?.credits ?? 0) <= 0;

  return (
    <div className="processor-container animate-fade-in-up" style={{animationDelay: '0.2s'}}>
      <div className="glass-panel input-panel">
        <form onSubmit={handleSubmit} className="input-form-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {user && (
            <div className="credit-balance-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '4px' }}>
              <span style={{ fontSize: '13px', color: '#9ca3af' }}>Platform Token & Quota</span>
              <div className="credit-token-badge" style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.2)', padding: '4px 12px', borderRadius: '12px', color: '#facc15', fontWeight: '700', fontSize: '14px' }}>
                <span style={{ fontSize: '16px' }}>🪙</span>
                <span>{user.role === 'admin' ? 'Unlimited Credit' : `${user.credits} Kredit Tersisa`}</span>
              </div>
            </div>
          )}

          {hasNoCredits && (
            <div className="animate-shake" style={{ padding: '12px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#fca5a5', fontSize: '13px', textAlign: 'center', fontWeight: '500' }}>
              ⚠️ Saldo kredit Anda habis! Silakan hubungi Admin untuk menambah kredit.
            </div>
          )}

          <div className="input-form" style={{ display: 'flex', gap: '12px', width: '100%' }}>
            <div className="input-wrapper">
              <Film className="input-icon text-red-500" style={{color: '#ff0000'}} size={24} />
              <input 
                type="url" 
                placeholder="Paste link YouTube di sini (misal: https://youtube.com/watch?...)" 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isProcessing || hasNoCredits}
                required
              />
            </div>
            
            <button 
              type="submit" 
              className={`btn-primary ${isProcessing ? 'pulse-animation' : ''}`}
              disabled={isProcessing || hasNoCredits}
            >
              {isProcessing ? (
                <span className="flex-center"><Loader2 className="spinner" size={20} /> Memproses...</span>
              ) : (
                <span className="flex-center"><Wand2 size={20} /> Buat Klip Viral</span>
              )}
            </button>
          </div>

          <div className="options-wrapper animate-fade-in-up" style={{ animationDelay: '0.3s', display: 'flex', flexDirection: 'column', gap: '16px', paddingLeft: '8px' }}>
            <label className="modern-toggle" style={{ marginTop: 0 }}>
              <input 
                type="checkbox" 
                checked={withSubtitle}
                onChange={(e) => setWithSubtitle(e.target.checked)}
                disabled={isProcessing}
              />
              <span className="toggle-slider"></span>
              <span className="toggle-label">Render Dengan Auto-Subtitle (Teks Kuning)</span>
            </label>

            <div className="duration-selector" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '14px', color: '#9ca3af', fontWeight: '500' }}>Pilih Durasi:</span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {[6, 15, 30, 60, 120, 180].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setClipDuration(val)}
                    disabled={isProcessing}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '8px',
                      border: '1px solid ' + (clipDuration === val ? '#ff0000' : 'rgba(255, 255, 255, 0.1)'),
                      background: clipDuration === val ? 'rgba(255, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                      color: clipDuration === val ? '#fff' : '#9ca3af',
                      cursor: isProcessing ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      fontWeight: clipDuration === val ? '600' : '400'
                    }}
                  >
                    {val < 60 ? `${val} Detik` : `${val/60} Menit`}
                  </button>
                ))}
              </div>
            </div>

            <div className="layout-selector" style={{ marginTop: '8px' }}>
              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#fff', margin: '0 0 6px 0' }}>Mode Layout</h3>
                <p style={{ fontSize: '13px', color: '#9ca3af', margin: 0 }}>Pilih look akhir sesuai kontenmu.</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                {[
                  { id: 'auto_magic', title: 'Auto Magic', desc: 'AI menilai konten, pilih blur / reframe terbaik tanpa mikir.', badge: 'DISARANKAN' },
                  { id: 'gaussian_blur', title: 'Gaussian Blur', desc: 'Latar belakang blur lembut + fokus ke frame utama.', badge: '' },
                  { id: 'auto_reframe', title: 'Auto Reframe', desc: 'Crop dinamis mengikuti wajah & objek (butuh video high-res).', badge: 'BETA' }
                ].map(mode => (
                  <div 
                    key={mode.id}
                    onClick={() => !isProcessing && setLayoutMode(mode.id)}
                    style={{
                      background: layoutMode === mode.id ? 'rgba(99, 102, 241, 0.05)' : 'rgba(255, 255, 255, 0.03)',
                      border: '2px solid ' + (layoutMode === mode.id ? '#6366f1' : 'transparent'),
                      boxShadow: layoutMode === mode.id ? '0 0 0 1px rgba(99, 102, 241, 0.2)' : 'inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
                      borderRadius: '12px',
                      padding: '20px 16px',
                      cursor: isProcessing ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      position: 'relative'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '600', color: '#fff' }}>{mode.title}</h4>
                      {mode.badge && (
                        <span style={{ fontSize: '10px', fontWeight: '700', color: '#6366f1', letterSpacing: '0.5px' }}>{mode.badge}</span>
                      )}
                    </div>
                    <p style={{ margin: 0, fontSize: '13px', color: '#9ca3af', lineHeight: '1.5' }}>{mode.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </form>
      </div>

      {isProcessing && (
        <div className="loading-indicator glass-panel animate-fade-in-up">
          <div className="loading-steps" style={{ marginBottom: '16px' }}>
            <div className={`step ${loadingProgress > 0 ? 'active' : ''}`}>Mengunduh Transkrip...</div>
            <div className={`step ${loadingProgress > 35 ? 'active' : ''}`}>AI Menganalisis Momen...</div>
            <div className={`step ${loadingProgress > 75 ? 'active' : ''}`}>Memotong Video & Subtitle...</div>
          </div>
          <div style={{ textAlign: 'center', fontSize: '28px', fontWeight: 'bold', color: '#6366f1', marginBottom: '8px' }}>
            {Math.round(loadingProgress)}%
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${loadingProgress}%`, height: '100%', background: 'linear-gradient(90deg, #6366f1, #a855f7)', transition: 'width 0.2s ease-out' }}></div>
          </div>
        </div>
      )}

      {clips && (
        <div className="results-container animate-fade-in-up">
          <h2 className="results-title">AI Menemukan <span className="gradient-text">{clips.length} Klip Berpotensi Viral</span></h2>
          
          <div className="clips-grid">
            {clips.map(clip => (
              <div key={clip.id} className="clip-card glass-panel">
                <div className="clip-thumbnail">
                  <img src={clip.thumbnail} alt={clip.title} />
                  <div className="play-overlay">
                    <Play fill="white" size={32} />
                  </div>
                  <span className="duration-badge">{clip.duration}</span>
                </div>
                <div className="clip-info">
                  <div className="clip-header">
                    <span className="viral-score">🔥 {clip.score}</span>
                  </div>
                  <h3 className="clip-title">{clip.title}</h3>
                  <p className="clip-reason">{clip.viralReason}</p>
                  
                  <div className="clip-actions">
                    {clip.download_url && clip.download_url !== "#" ? (
                      <a href={clip.download_url} download target="_blank" rel="noreferrer" style={{textDecoration: 'none'}}>
                        <button className="btn-primary flex-center full-width" style={{marginTop: '16px'}}>
                          <Download size={18} /> Download (9:16)
                        </button>
                      </a>
                    ) : (
                        <button className="btn-primary flex-center full-width" style={{marginTop: '16px'}} disabled>
                          <Download size={18} /> (Menunggu API Key)
                        </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoProcessor;
