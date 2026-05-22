import React from 'react';
import { Scissors, LogOut, Shield, User } from 'lucide-react';
import './Header.css';

const Header = ({ user, onLogout, currentView, onViewChange, onTopUpClick }) => {
  return (
    <header className="header animate-fade-in-up">
      <div 
        className="logo" 
        onClick={() => user && onViewChange('dashboard')} 
        style={{ cursor: user ? 'pointer' : 'default' }}
      >
        <Scissors className="logo-icon gradient-text" size={32} />
        <span className="logo-text">AutoClip<span className="gradient-text">.AI</span></span>
      </div>
      
      <nav className="nav-links">
        {user ? (
          <div className="user-profile-menu" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {user.role !== 'admin' && (
              <button 
                onClick={onTopUpClick} 
                className="btn-primary" 
                style={{ 
                  fontSize: '0.85rem', 
                  padding: '6px 14px', 
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #00b4d8 0%, #0077b6 100%)',
                  boxShadow: '0 4px 12px rgba(0, 180, 216, 0.25)',
                  minHeight: 'auto',
                  border: 'none',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                TopUp Saldo
              </button>
            )}
            
            <div 
              className="user-info-badge" 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px', 
                background: 'rgba(255, 255, 255, 0.05)', 
                padding: '6px 12px', 
                borderRadius: '20px', 
                border: '1px solid rgba(255,255,255,0.08)' 
              }}
            >
              {user.role === 'admin' ? (
                <Shield size={14} style={{ color: '#9b4dff' }} />
              ) : (
                <User size={14} style={{ color: '#00e5ff' }} />
              )}
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>
                {user.username}
              </span>
            </div>

            {user.role === 'admin' && (
              currentView === 'dashboard' ? (
                <button 
                  onClick={() => onViewChange('admin_dashboard')} 
                  className="btn-secondary" 
                  style={{ fontSize: '0.85rem', padding: '6px 12px', borderRadius: '8px' }}
                >
                  Kelola User
                </button>
              ) : (
                <button 
                  onClick={() => onViewChange('dashboard')} 
                  className="btn-secondary" 
                  style={{ fontSize: '0.85rem', padding: '6px 12px', borderRadius: '8px' }}
                >
                  Dashboard Video
                </button>
              )
            )}

            <button 
              onClick={onLogout} 
              className="btn-logout flex-center"
              title="Logout"
              style={{
                background: 'none',
                border: 'none',
                color: '#ef4444',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                e.currentTarget.style.transform = 'scale(1.05)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'none';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              <LogOut size={18} />
            </button>
          </div>
        ) : currentView === 'landing' ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <a href="#features" style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textDecoration: 'none', transition: 'color 0.2s' }} onMouseEnter={(e) => e.target.style.color = 'var(--accent)'} onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}>Fitur</a>
            <a href="#pricing" style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textDecoration: 'none', transition: 'color 0.2s' }} onMouseEnter={(e) => e.target.style.color = 'var(--accent)'} onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}>Harga</a>
            <button className="btn-primary" onClick={() => onViewChange('login')} style={{ fontSize: '0.85rem', padding: '6px 14px', borderRadius: '8px', cursor: 'pointer', minHeight: 'auto' }}>
              Masuk
            </button>
          </div>
        ) : (
          <button className="btn-secondary" onClick={() => onViewChange('landing')} style={{ fontSize: '0.85rem', padding: '6px 14px', borderRadius: '8px', cursor: 'pointer' }}>
            Kembali ke Beranda
          </button>
        )}
      </nav>
    </header>
  );
};

export default Header;
