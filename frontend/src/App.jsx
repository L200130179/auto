import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import VideoProcessor from './components/VideoProcessor';
import Login from './components/Login';
import AdminPanel from './components/AdminPanel';
import TopUpModal from './components/TopUpModal';
import LandingPage from './components/LandingPage';
import './App.css';

function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('autoclip_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [currentView, setCurrentView] = useState(() => {
    const saved = localStorage.getItem('autoclip_user');
    if (saved) return 'dashboard';
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('admin') === '1') return 'login';
    return 'landing';
  });

  const [topUpInstruction, setTopUpInstruction] = useState('');
  const [isTopUpOpen, setIsTopUpOpen] = useState(false);

  useEffect(() => {
    axios.get('/api/settings')
      .then(res => {
        setTopUpInstruction(res.data.topup_instruction || '');
      })
      .catch(err => {
        console.error('Error fetching settings:', err);
      });
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem('autoclip_user', JSON.stringify(userData));
    setCurrentView('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('autoclip_user');
    setCurrentView('login');
  };

  const handleUpdateCredits = (newCredits) => {
    setUser(prev => {
      if (!prev) return null;
      const updated = { ...prev, credits: newCredits };
      localStorage.setItem('autoclip_user', JSON.stringify(updated));
      return updated;
    });
  };

  const handleSettingsSaved = (newInstruction) => {
    setTopUpInstruction(newInstruction);
  };

  return (
    <div className="app-container">
      <Header 
        user={user} 
        onLogout={handleLogout} 
        currentView={currentView} 
        onViewChange={setCurrentView} 
        onTopUpClick={() => setIsTopUpOpen(true)}
      />
      
      <main className="main-content">
        {currentView === 'landing' && (
          <LandingPage onGetStarted={() => setCurrentView('login')} />
        )}

        {currentView === 'login' && (
          <Login onLoginSuccess={handleLoginSuccess} />
        )}

        {currentView === 'dashboard' && (
          <>
            <div className="hero-section animate-fade-in-up">
              <h1 className="hero-title">
                Ubah Video Panjang Jadi <span className="gradient-text">Klip Viral</span>
              </h1>
              <p className="hero-subtitle">
                Cukup masukkan link YouTube, AI AutoClip akan otomatis mencari momen terbaik untuk TikTok, Reels, dan Shorts.
              </p>
            </div>
            <VideoProcessor user={user} onUpdateCredits={handleUpdateCredits} />
          </>
        )}

        {currentView === 'admin_dashboard' && (
          <AdminPanel 
            onBackToDashboard={() => setCurrentView('dashboard')} 
            onSettingsSaved={handleSettingsSaved}
          />
        )}
      </main>
      
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} AutoClip AI. All rights reserved.</p>
      </footer>

      <TopUpModal 
        isOpen={isTopUpOpen} 
        onClose={() => setIsTopUpOpen(false)} 
        instruction={topUpInstruction} 
      />
    </div>
  );
}

export default App;
