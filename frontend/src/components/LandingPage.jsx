import React from 'react';
import { Sparkles, Cpu, Zap, Video, Layers, ShieldCheck, TrendingUp, CheckCircle2, ArrowRight } from 'lucide-react';
import './LandingPage.css';

const LandingPage = ({ onGetStarted }) => {
  return (
    <div className="landing-page-container">
      
      {/* 1. HERO SECTION */}
      <section className="landing-hero animate-fade-in-up">
        <div className="hero-glow-1"></div>
        <div className="hero-glow-2"></div>
        
        <div className="badge hero-badge">
          <Sparkles size={14} className="sparkle-icon" />
          <span>SISTEM GENERASI KLIP OTOMATIS BERBASIS AI</span>
        </div>
        
        <h1 className="hero-main-title">
          Revolusi Content Creation:<br />
          Ubah Video Panjang Jadi <span className="gradient-text">Klip Viral</span>
        </h1>
        
        <p className="hero-description">
          Didukung AI pintar untuk menganalisis transkrip, mendeteksi momen paling menarik, dan memotong video secara vertikal otomatis untuk TikTok, Reels, dan Shorts dalam hitungan detik.
        </p>
        
        <div className="hero-actions">
          <button onClick={onGetStarted} className="btn-primary start-now-btn">
            Mulai Gratis Sekarang <ArrowRight size={18} style={{ marginLeft: '8px' }} />
          </button>
          <a href="#features" className="btn-secondary learn-more-btn">
            Pelajari Fitur
          </a>
        </div>
        
        {/* Mockup Dashboard Preview */}
        <div className="hero-mockup-wrapper glass-panel">
          <div className="mockup-header">
            <div className="mockup-dots">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
            </div>
            <div className="mockup-title">autoclip_dashboard_preview.exe</div>
          </div>
          <div className="mockup-body">
            <div className="mockup-input-box">
              <span className="mockup-label">YouTube Link:</span>
              <div className="mockup-input-field">
                https://www.youtube.com/watch?v=viral_clip_source
              </div>
            </div>
            <div className="mockup-processing-bar">
              <span className="pulse-text">AI memindai momen terbaik dan mencocokkan transkrip...</span>
              <div className="progress-track">
                <div className="progress-fill"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. STATS SECTION */}
      <section className="stats-section">
        <div className="stat-card glass-panel">
          <h3>90%</h3>
          <p>Menghemat Waktu Edit</p>
        </div>
        <div className="stat-card glass-panel">
          <h3>10x</h3>
          <p>Meningkatkan Reach Konten</p>
        </div>
        <div className="stat-card glass-panel">
          <h3>1 Klik</h3>
          <p>Hasil Klip Siap Download</p>
        </div>
      </section>

      {/* 3. FEATURES SECTION */}
      <section id="features" className="features-section">
        <div className="section-header">
          <h2 className="section-title">Kenapa Memilih <span className="gradient-text">AutoClip.AI</span>?</h2>
          <p className="section-subtitle">Semua alat yang Anda butuhkan untuk mendominasi algoritma media sosial tanpa menghabiskan waktu berjam-jam mengedit.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card glass-panel">
            <div className="feature-icon-wrapper blue-icon">
              <Cpu size={24} />
            </div>
            <h3>AI Transcript Scanner</h3>
            <p>Algoritma kami menganalisis transkrip pembicaraan secara instan untuk melacak bagian terlucu, momen mengejutkan, atau kutipan motivasi terbaik.</p>
          </div>

          <div className="feature-card glass-panel">
            <div className="feature-icon-wrapper cyan-icon">
              <Video size={24} />
            </div>
            <h3>Smart Vertical Auto-Crop</h3>
            <p>Otomatis memotong area video horizontal menjadi resolusi vertikal 9:16 dengan menempatkan fokus visual di tengah layar.</p>
          </div>

          <div className="feature-card glass-panel">
            <div className="feature-icon-wrapper purple-icon">
              <Zap size={24} />
            </div>
            <h3>Super Fast Rendering</h3>
            <p>Didukung oleh engine pemrosesan video berkecepatan tinggi di backend untuk menyajikan klip Anda dalam hitungan detik.</p>
          </div>

          <div className="feature-card glass-panel">
            <div className="feature-icon-wrapper green-icon">
              <Layers size={24} />
            </div>
            <h3>Durasi Dinamis</h3>
            <p>Sesuaikan durasi klip Anda mulai dari 6 detik hingga klip yang lebih panjang untuk optimasi retensi penonton yang maksimal.</p>
          </div>
        </div>
      </section>

      {/* 4. CARA KERJA SECTION */}
      <section className="steps-section">
        <div className="section-header">
          <h2 className="section-title">Cara Kerja <span className="gradient-text">AutoClip</span></h2>
          <p className="section-subtitle">Hanya butuh 3 langkah mudah untuk meluncurkan ratusan klip pendek berkualitas tinggi.</p>
        </div>

        <div className="steps-timeline">
          <div className="step-item">
            <div className="step-number-badge">1</div>
            <h3>Tempel Link YouTube</h3>
            <p>Salin URL video YouTube yang ingin Anda ambil klipnya dan masukkan ke kolom input autoclip.</p>
          </div>
          <div className="step-item">
            <div className="step-number-badge">2</div>
            <h3>AI Melakukan Pemotongan</h3>
            <p>Sistem AI kami mendeteksi durasi terbaik, memproses audio, dan merender video secara vertikal.</p>
          </div>
          <div className="step-item">
            <div className="step-number-badge">3</div>
            <h3>Unduh Klip Viral</h3>
            <p>Hasil potongan langsung siap diunduh dan diposting ke TikTok, YouTube Shorts, atau Instagram Reels.</p>
          </div>
        </div>
      </section>

      {/* 5. PRICING SECTION */}
      <section id="pricing" className="pricing-section">
        <div className="section-header">
          <h2 className="section-title">Paket Kredit <span className="gradient-text">Kreator</span></h2>
          <p className="section-subtitle">Dapatkan kredit instan dengan harga terjangkau untuk menggerakkan otomatisasi klip Anda.</p>
        </div>

        <div className="pricing-grid">
          
          {/* Plan 1 */}
          <div className="price-card glass-panel">
            <div className="price-badge">Trial</div>
            <h3>Akun Trial Gratis</h3>
            <div className="price-val">Rp 0</div>
            <p className="price-desc">Coba sistem kami secara gratis tanpa risiko.</p>
            <ul className="price-features">
              <li><CheckCircle2 size={16} className="check-icon" /> 1 Kredit Token Gratis</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Pemrosesan Klip Cepat</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Deteksi Keamanan Perangkat</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Kualitas Video HD 9:16</li>
            </ul>
            <button onClick={onGetStarted} className="btn-secondary price-btn">Mulai Coba Gratis</button>
          </div>

          {/* Plan 2 - Recommended */}
          <div className="price-card glass-panel recommended-card">
            <div className="pop-badge">TERPOPULER</div>
            <div className="price-badge highlight-badge">Starter Pack</div>
            <h3>Paket Starter</h3>
            <div className="price-val">Rp 20.000</div>
            <p className="price-desc">Sangat cocok untuk pembuat konten pemula.</p>
            <ul className="price-features">
              <li><CheckCircle2 size={16} className="check-icon" /> 10 Kredit Token</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Pemrosesan Klip Cepat</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Akses Fitur Autoclip 6 Detik</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Kualitas Video HD 9:16</li>
            </ul>
            <button onClick={onGetStarted} className="btn-primary price-btn">Beli Sekarang</button>
          </div>

          {/* Plan 3 */}
          <div className="price-card glass-panel">
            <div className="price-badge">Pro Creator</div>
            <h3>Paket Pro</h3>
            <div className="price-val">Rp 50.000</div>
            <p className="price-desc">Pilihan terbaik untuk kreator konten aktif harian.</p>
            <ul className="price-features">
              <li><CheckCircle2 size={16} className="check-icon" /> 30 Kredit Token</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Pemrosesan Klip Prioritas Utama</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Akses Fitur Autoclip Lengkap</li>
              <li><CheckCircle2 size={16} className="check-icon" /> Dukungan CS Prioritas</li>
            </ul>
            <button onClick={onGetStarted} className="btn-secondary price-btn">Beli Sekarang</button>
          </div>

        </div>
      </section>

      {/* 6. FINAL CTA */}
      <section className="final-cta">
        <div className="cta-glow"></div>
        <h2>Siap Untuk <span className="gradient-text">Go Viral</span>?</h2>
        <p>Bergabunglah dengan ratusan creator sukses yang mengotomatiskan klip pendek mereka menggunakan AI AutoClip.</p>
        <button onClick={onGetStarted} className="btn-primary cta-btn">
          Mulai Pendaftaran Akun <ArrowRight size={18} style={{ marginLeft: '8px' }} />
        </button>
      </section>

    </div>
  );
};

export default LandingPage;
