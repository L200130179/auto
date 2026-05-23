import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, UserPlus, Shield, Calendar, Lock, User, Loader2, ArrowLeft, Edit, Trash2, X, Mail } from 'lucide-react';
import './AdminPanel.css';

const AdminPanel = ({ onBackToDashboard, onSettingsSaved }) => {
  const [users, setUsers] = useState([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('creator');
  const [newCredits, setNewCredits] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitLoading, setIsSubmitLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // TopUp settings state
  const [topupInstruction, setTopupInstruction] = useState('');
  const [isSettingsSubmitLoading, setIsSettingsSubmitLoading] = useState(false);

  // Edit user modal states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editUsername, setEditUsername] = useState('');
  const [editNewUsername, setEditNewUsername] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editPassword, setEditPassword] = useState('');
  const [editRole, setEditRole] = useState('creator');
  const [editCredits, setEditCredits] = useState(10);
  const [isEditLoading, setIsEditLoading] = useState(false);

  // Gemini API Key state
  const [geminiKeys, setGeminiKeys] = useState(Array(10).fill(''));
  const [isGeminiSubmitLoading, setIsGeminiSubmitLoading] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [isCleanLoading, setIsCleanLoading] = useState(false);
  const [autoCleanup, setAutoCleanup] = useState(true);
  const [isToggleLoading, setIsToggleLoading] = useState(false);

  const fetchUsers = () => {
    setIsLoading(true);
    axios.get('/api/admin/users')
      .then(res => {
        setUsers(res.data.users || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError('Gagal memuat daftar user.');
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchUsers();
    
    // Fetch current settings
    axios.get('/api/settings')
      .then(res => {
        setTopupInstruction(res.data.topup_instruction || '');
        setAutoCleanup(res.data.auto_cleanup !== false);
      })
      .catch(err => {
        console.error('Error fetching settings in AdminPanel:', err);
      });

    // Fetch current gemini keys
    axios.get('/api/admin/gemini-key')
      .then(res => {
        if (res.data.gemini_keys && Array.isArray(res.data.gemini_keys)) {
          setGeminiKeys(res.data.gemini_keys);
        } else {
          const raw = res.data.gemini_key || '';
          const parsed = raw.split(',').map(k => k.trim());
          const padded = [...parsed];
          while (padded.length < 10) padded.push('');
          setGeminiKeys(padded.slice(0, 10));
        }
      })
      .catch(err => {
        console.error('Error fetching gemini keys in AdminPanel:', err);
      });
  }, []);

  const handleAddUser = (e) => {
    e.preventDefault();
    if (!newUsername || !newPassword) return;

    setIsSubmitLoading(true);
    setError('');
    setSuccessMsg('');

    axios.post('/api/admin/users', {
      username: newUsername,
      password: newPassword,
      role: newRole,
      credits: newCredits
    })
      .then(res => {
        setIsSubmitLoading(false);
        setSuccessMsg(`User "${newUsername}" berhasil ditambahkan!`);
        setNewUsername('');
        setNewPassword('');
        setNewRole('creator');
        setNewCredits(10);
        // Refresh list
        fetchUsers();
      })
      .catch(err => {
        setIsSubmitLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal menambahkan user.';
        setError(errMsg);
      });
  };

  const handleInlineCreditChange = (username, value) => {
    setUsers(prev => prev.map(u => u.username === username ? { ...u, credits: value } : u));
  };

  const handleUpdateCreditSubmit = (username, credits) => {
    setError('');
    setSuccessMsg('');
    axios.post('/api/admin/users/update-credit', {
      username,
      credits
    })
      .then(res => {
        setSuccessMsg(`Kredit untuk "${username}" berhasil diperbarui menjadi ${credits}!`);
        fetchUsers();
      })
      .catch(err => {
        const errMsg = err.response?.data?.error || 'Gagal memperbarui kredit.';
        setError(errMsg);
      });
  };

  const handleUpdateSettings = (e) => {
    e.preventDefault();
    if (!topupInstruction) return;

    setIsSettingsSubmitLoading(true);
    setError('');
    setSuccessMsg('');

    axios.post('/api/admin/settings', {
      topup_instruction: topupInstruction
    })
      .then(res => {
        setIsSettingsSubmitLoading(false);
        setSuccessMsg('Pengaturan TopUp Saldo berhasil disimpan!');
        if (onSettingsSaved) {
          onSettingsSaved(topupInstruction);
        }
      })
      .catch(err => {
        setIsSettingsSubmitLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal menyimpan pengaturan.';
        setError(errMsg);
      });
  };

  const handleDeleteUser = (username) => {
    if (!window.confirm(`Apakah Anda yakin ingin menghapus user "${username}"? Setelah dihapus, perangkat yang bersangkutan dapat mendaftar kembali.`)) {
      return;
    }
    setError('');
    setSuccessMsg('');
    axios.delete('/api/admin/users', { data: { username } })
      .then(res => {
        setSuccessMsg(res.data.message || `User "${username}" berhasil dihapus.`);
        fetchUsers();
      })
      .catch(err => {
        const errMsg = err.response?.data?.error || 'Gagal menghapus user.';
        setError(errMsg);
      });
  };

  const openEditModal = (userObj) => {
    setEditUsername(userObj.username);
    setEditNewUsername(userObj.username);
    setEditEmail(userObj.email || '');
    setEditPassword(userObj.password || '');
    setEditRole(userObj.role || 'creator');
    setEditCredits(userObj.credits !== undefined ? userObj.credits : 10);
    setIsEditModalOpen(true);
  };

  const handleEditUserSubmit = (e) => {
    e.preventDefault();
    if (!editUsername) return;
    setIsEditLoading(true);
    setError('');
    setSuccessMsg('');
    axios.post('/api/admin/users/update', {
      username: editUsername,
      new_username: editNewUsername,
      email: editEmail,
      password: editPassword,
      role: editRole,
      credits: editCredits
    })
      .then(res => {
        setIsEditLoading(false);
        setIsEditModalOpen(false);
        setSuccessMsg(`User "${editUsername}" berhasil diperbarui!`);
        fetchUsers();
      })
      .catch(err => {
        setIsEditLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal memperbarui user.';
        setError(errMsg);
      });
  };

  const handleKeyChange = (index, value) => {
    setGeminiKeys(prev => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  };

  const handleUpdateGeminiKey = (e) => {
    e.preventDefault();
    const hasKey = geminiKeys.some(k => k.trim() !== '');
    if (!hasKey) {
      setError('Minimal harus mengisi 1 Gemini API Key.');
      return;
    }

    setIsGeminiSubmitLoading(true);
    setError('');
    setSuccessMsg('');

    axios.post('/api/admin/gemini-key', {
      gemini_keys: geminiKeys
    })
      .then(res => {
        setIsGeminiSubmitLoading(false);
        setSuccessMsg(res.data.message || 'GEMINI_API_KEY berhasil diperbarui!');
      })
      .catch(err => {
        setIsGeminiSubmitLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal memperbarui GEMINI_API_KEY.';
        setError(errMsg);
      });
  };

  const handleCleanStaticFiles = () => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus semua berkas video dan audio di folder static server sekarang? Tindakan ini tidak dapat dibatalkan.')) {
      return;
    }
    setIsCleanLoading(true);
    setError('');
    setSuccessMsg('');
    axios.post('/api/admin/clean-static')
      .then(res => {
        setIsCleanLoading(false);
        setSuccessMsg(res.data.message || 'Folder static berhasil dibersihkan!');
      })
      .catch(err => {
        setIsCleanLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal membersihkan folder static.';
        setError(errMsg);
      });
  };

  const handleToggleAutoCleanup = (newValue) => {
    setIsToggleLoading(true);
    setError('');
    setSuccessMsg('');
    axios.post('/api/admin/toggle-cleanup', {
      auto_cleanup: newValue
    })
      .then(res => {
        setIsToggleLoading(false);
        setAutoCleanup(res.data.auto_cleanup);
        setSuccessMsg(res.data.message || 'Pengaturan auto-cleanup berhasil diperbarui!');
      })
      .catch(err => {
        setIsToggleLoading(false);
        const errMsg = err.response?.data?.error || 'Gagal mengubah pengaturan auto-cleanup.';
        setError(errMsg);
      });
  };

  return (
    <div className="admin-panel-container animate-fade-in-up">
      <div className="admin-actions">
        <button onClick={onBackToDashboard} className="btn-secondary back-btn flex-center">
          <ArrowLeft size={16} style={{ marginRight: '6px' }} /> Kembali ke Dashboard
        </button>
      </div>

      <div className="admin-grid">
        {/* Left Side: Create User Form & Settings Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Card 1: Create User Form */}
          <div className="admin-card glass-panel form-card">
            <div className="card-header">
              <div className="card-icon-container">
                <UserPlus size={20} className="card-icon" />
              </div>
              <div>
                <h3>Tambah Akses User</h3>
                <p>Berikan hak akses untuk Creator atau Admin baru</p>
              </div>
            </div>

            {error && <div className="admin-alert error-alert animate-shake">⚠️ {error}</div>}
            {successMsg && <div className="admin-alert success-alert">✅ {successMsg}</div>}

            <form onSubmit={handleAddUser} className="admin-form">
              <div className="form-group">
                <label>Username</label>
                <div className="input-icon-wrapper">
                  <User size={18} className="input-field-icon" />
                  <input
                    type="text"
                    placeholder="Masukkan username..."
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    required
                    disabled={isSubmitLoading}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Password</label>
                <div className="input-icon-wrapper">
                  <Lock size={18} className="input-field-icon" />
                  <input
                    type="password"
                    placeholder="Masukkan password..."
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    disabled={isSubmitLoading}
                  />
                </div>
              </div>

              {newRole !== 'admin' && (
                <div className="form-group animate-fade-in-up">
                  <label>Kredit Awal</label>
                  <div className="input-icon-wrapper">
                    <span className="input-field-icon" style={{ fontSize: '14px', fontWeight: 'bold', left: '14px' }}>🪙</span>
                    <input
                      type="number"
                      placeholder="Kredit awal (default 10)..."
                      value={newCredits}
                      onChange={(e) => setNewCredits(parseInt(e.target.value) || 0)}
                      min="0"
                      required
                      disabled={isSubmitLoading}
                      style={{ paddingLeft: '38px' }}
                    />
                  </div>
                </div>
              )}

              <div className="form-group">
                <label>Role</label>
                <div className="role-selector">
                  <label className={`role-option ${newRole === 'creator' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="role"
                      value="creator"
                      checked={newRole === 'creator'}
                      onChange={() => {
                        setNewRole('creator');
                        setNewCredits(10);
                      }}
                    />
                    <span>Creator</span>
                  </label>
                  <label className={`role-option ${newRole === 'admin' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="role"
                      value="admin"
                      checked={newRole === 'admin'}
                      onChange={() => {
                        setNewRole('admin');
                        setNewCredits(9999);
                      }}
                    />
                    <span>Admin</span>
                  </label>
                </div>
              </div>

              <button type="submit" className="btn-primary submit-btn flex-center" disabled={isSubmitLoading}>
                {isSubmitLoading ? (
                  <>
                    <Loader2 className="spinner" size={18} /> Menyimpan...
                  </>
                ) : (
                  'Simpan User'
                )}
              </button>
            </form>
          </div>

          {/* Card 2: Settings Configuration Form */}
          <div className="admin-card glass-panel settings-card">
            <div className="card-header">
              <div className="card-icon-container" style={{ background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.2)' }}>
                <span style={{ fontSize: '18px' }}>⚙️</span>
              </div>
              <div>
                <h3>Konfigurasi TopUp Saldo</h3>
                <p>Ubah instruksi popup transfer yang muncul di dashboard creator</p>
              </div>
            </div>

            <form onSubmit={handleUpdateSettings} className="admin-form">
              <div className="form-group">
                <label>Instruksi Transfer</label>
                <textarea
                  placeholder="Masukkan instruksi topup..."
                  value={topupInstruction}
                  onChange={(e) => setTopupInstruction(e.target.value)}
                  required
                  disabled={isSettingsSubmitLoading}
                  rows={5}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '10px',
                    color: 'var(--text-main)',
                    fontFamily: 'inherit',
                    fontSize: '0.9rem',
                    resize: 'vertical',
                    lineHeight: '1.5',
                    transition: 'all 0.3s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
                />
              </div>

              <button type="submit" className="btn-primary submit-btn flex-center" disabled={isSettingsSubmitLoading}>
                {isSettingsSubmitLoading ? (
                  <>
                    <Loader2 className="spinner" size={18} /> Menyimpan...
                  </>
                ) : (
                  'Simpan Instruksi'
                )}
              </button>
            </form>
          </div>

          {/* Card 3: Gemini API Key Form */}
          <div className="admin-card glass-panel gemini-card">
            <div className="card-header">
              <div className="card-icon-container" style={{ background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                <span style={{ fontSize: '18px' }}>🔑</span>
              </div>
              <div>
                <h3>Pengaturan Gemini API Key</h3>
                <p>Ubah kunci API Gemini untuk memproses video secara instan</p>
              </div>
            </div>

            <form onSubmit={handleUpdateGeminiKey} className="admin-form">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '400px', overflowY: 'auto', paddingRight: '6px', marginBottom: '16px' }}>
                {geminiKeys.map((key, idx) => (
                  <div className="form-group" key={idx} style={{ margin: 0 }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Gemini API Key #{idx + 1}</label>
                    <div className="input-icon-wrapper">
                      <Lock size={14} className="input-field-icon" style={{ left: '12px' }} />
                      <input
                        type={showGeminiKey ? "text" : "password"}
                        placeholder={`Masukkan Gemini API Key #${idx + 1}...`}
                        value={key}
                        onChange={(e) => handleKeyChange(idx, e.target.value)}
                        disabled={isGeminiSubmitLoading}
                        style={{ paddingLeft: '32px', fontSize: '0.85rem', height: '36px' }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '8px',
                    color: 'var(--text-main)',
                    padding: '8px 16px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 'bold',
                    transition: 'all 0.2s',
                    flexShrink: 0
                  }}
                >
                  {showGeminiKey ? 'Sembunyikan Sandi' : 'Tampilkan Sandi'}
                </button>

                <button type="submit" className="btn-primary submit-btn flex-center" disabled={isGeminiSubmitLoading} style={{ margin: 0, flex: 1 }}>
                  {isGeminiSubmitLoading ? (
                    <>
                      <Loader2 className="spinner" size={18} /> Menyimpan...
                    </>
                  ) : (
                    'Simpan API Key'
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Card 4: Pemeliharaan Server */}
          <div className="admin-card glass-panel maintenance-card">
            <div className="card-header">
              <div className="card-icon-container" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                <span style={{ fontSize: '18px' }}>🧹</span>
              </div>
              <div>
                <h3>Pemeliharaan Server</h3>
                <p>Bersihkan berkas media lama secara berkala atau manual</p>
              </div>
            </div>

            <div className="admin-form">
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                  Sistem otomatis menghapus berkas video/audio di folder <code style={{ color: 'var(--accent)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>backend/static</code> yang berumur lebih dari <strong>1 jam</strong>.
                </label>
              </div>

              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  marginBottom: '20px', 
                  padding: '12px 16px', 
                  borderRadius: '10px', 
                  background: 'rgba(255, 255, 255, 0.02)', 
                  border: '1px solid var(--glass-border)' 
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '16px' }}>{isToggleLoading ? '⏳' : '🔄'}</span>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: '600' }}>Pembersihan Otomatis</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hapus file &gt; 1 jam secara berkala</div>
                  </div>
                </div>
                <label className="switch-container" style={{ position: 'relative', display: 'inline-block', width: '46px', height: '24px', margin: 0 }}>
                  <input
                    type="checkbox"
                    checked={autoCleanup}
                    disabled={isToggleLoading}
                    onChange={(e) => handleToggleAutoCleanup(e.target.checked)}
                    style={{ opacity: 0, width: 0, height: 0 }}
                  />
                  <span 
                    style={{
                      position: 'absolute',
                      cursor: isToggleLoading ? 'not-allowed' : 'pointer',
                      top: 0, left: 0, right: 0, bottom: 0,
                      backgroundColor: autoCleanup ? '#00e5ff' : '#334155',
                      transition: '0.3s',
                      borderRadius: '24px',
                      boxShadow: autoCleanup ? '0 0 10px rgba(0, 229, 255, 0.3)' : 'none'
                    }}
                  >
                    <span 
                      style={{
                        position: 'absolute',
                        content: '""',
                        height: '18px', width: '18px',
                        left: autoCleanup ? '24px' : '4px',
                        bottom: '3px',
                        backgroundColor: '#ffffff',
                        transition: '0.3s',
                        borderRadius: '50%'
                      }}
                    />
                  </span>
                </label>
              </div>

              <button
                type="button"
                className="btn-primary submit-btn flex-center"
                style={{ background: 'linear-gradient(135deg, #ef4444, #b91c1c)', borderColor: '#ef4444' }}
                onClick={handleCleanStaticFiles}
                disabled={isCleanLoading}
              >
                {isCleanLoading ? (
                  <>
                    <Loader2 className="spinner" size={18} /> Membersihkan...
                  </>
                ) : (
                  <>
                    <Trash2 size={16} style={{ marginRight: '6px' }} /> Bersihkan Folder Static
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Users List */}
        <div className="admin-card glass-panel list-card">
          <div className="card-header">
            <div className="card-icon-container">
              <Users size={20} className="card-icon" />
            </div>
            <div>
              <h3>Daftar Pengguna Aktif</h3>
              <p>Pengguna terdaftar dengan akses ke AutoClip.AI</p>
            </div>
          </div>

          {isLoading ? (
            <div className="list-loading flex-center">
              <Loader2 className="spinner" size={32} />
              <span>Memuat data...</span>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Kredit</th>
                    <th>Tanggal Dibuat</th>
                    <th>Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                        Tidak ada user ditemukan.
                      </td>
                    </tr>
                  ) : (
                    users.map((u, i) => (
                      <tr key={i}>
                        <td className="username-cell">
                          <User size={14} style={{ marginRight: '6px', color: 'var(--accent)' }} />
                          {u.username}
                        </td>
                        <td style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                          <Mail size={13} style={{ marginRight: '6px', color: 'var(--text-muted)', verticalAlign: 'middle' }} />
                          {u.email || '-'}
                        </td>
                        <td>
                          <span className={`role-badge ${u.role === 'admin' ? 'admin' : 'creator'}`}>
                            {u.role === 'admin' ? <Shield size={10} style={{ marginRight: '4px' }} /> : null}
                            {u.role.toUpperCase()}
                          </span>
                        </td>
                        <td className="credits-cell">
                          {u.role === 'admin' ? (
                            <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Unlimited</span>
                          ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <input
                                type="number"
                                value={u.credits !== undefined ? u.credits : 10}
                                onChange={(e) => handleInlineCreditChange(u.username, parseInt(e.target.value) || 0)}
                                style={{
                                  width: '55px',
                                  background: 'rgba(0,0,0,0.3)',
                                  border: '1px solid rgba(255,255,255,0.08)',
                                  borderRadius: '6px',
                                  color: '#fff',
                                  padding: '4px 6px',
                                  fontSize: '13px',
                                  textAlign: 'center',
                                  fontWeight: '600'
                                }}
                              />
                              <button
                                onClick={() => handleUpdateCreditSubmit(u.username, u.credits)}
                                className="btn-primary"
                                style={{
                                  padding: '4px 8px',
                                  fontSize: '11px',
                                  borderRadius: '6px',
                                  minHeight: 'auto',
                                  background: 'linear-gradient(135deg, #eaac08 0%, #ca8a04 100%)',
                                  boxShadow: 'none'
                                }}
                              >
                                Simpan
                              </button>
                            </div>
                          )}
                        </td>
                        <td className="date-cell">
                          <Calendar size={14} style={{ marginRight: '6px', color: 'var(--text-muted)' }} />
                          {u.created_at ? new Date(u.created_at).toLocaleDateString('id-ID', {
                            year: 'numeric', month: 'short', day: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                          }) : '-'}
                        </td>
                        <td>
                          <div className="action-btn-group">
                            <button className="action-btn edit-btn-action" onClick={() => openEditModal(u)} title="Edit User">
                              <Edit size={14} />
                            </button>
                            <button className="action-btn delete-btn-action" onClick={() => handleDeleteUser(u.username)} title="Hapus User">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Edit User Modal Overlay */}
      {isEditModalOpen && (
        <div className="admin-modal-overlay">
          <div className="admin-modal glass-panel animate-fade-in-up">
            <div className="modal-header">
              <h3>Edit Detail User: <span style={{ color: 'var(--accent)' }}>{editUsername}</span></h3>
              <button className="close-modal-btn" onClick={() => setIsEditModalOpen(false)}>
                <X size={18} />
              </button>
            </div>
            
            <form onSubmit={handleEditUserSubmit} className="admin-form">
              <div className="form-group">
                <label>Username Baru</label>
                <div className="input-icon-wrapper">
                  <User size={18} className="input-field-icon" />
                  <input
                    type="text"
                    value={editNewUsername}
                    onChange={(e) => setEditNewUsername(e.target.value)}
                    required
                    disabled={isEditLoading}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Email</label>
                <div className="input-icon-wrapper">
                  <Mail size={18} className="input-field-icon" />
                  <input
                    type="email"
                    value={editEmail}
                    onChange={(e) => setEditEmail(e.target.value)}
                    required
                    disabled={isEditLoading}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Sandi Baru (Kosongkan jika tidak diubah)</label>
                <div className="input-icon-wrapper">
                  <Lock size={18} className="input-field-icon" />
                  <input
                    type="password"
                    placeholder="Sandi baru..."
                    value={editPassword}
                    onChange={(e) => setEditPassword(e.target.value)}
                    disabled={isEditLoading}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Kredit</label>
                <div className="input-icon-wrapper">
                  <span className="input-field-icon" style={{ fontSize: '14px', fontWeight: 'bold', left: '14px' }}>🪙</span>
                  <input
                    type="number"
                    value={editCredits}
                    onChange={(e) => setEditCredits(parseInt(e.target.value) || 0)}
                    min="0"
                    required
                    disabled={isEditLoading}
                    style={{ paddingLeft: '38px' }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Role</label>
                <div className="role-selector">
                  <label className={`role-option ${editRole === 'creator' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="editRole"
                      value="creator"
                      checked={editRole === 'creator'}
                      onChange={() => setEditRole('creator')}
                    />
                    <span>Creator</span>
                  </label>
                  <label className={`role-option ${editRole === 'admin' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="editRole"
                      value="admin"
                      checked={editRole === 'admin'}
                      onChange={() => setEditRole('admin')}
                    />
                    <span>Admin</span>
                  </label>
                </div>
              </div>

              <div className="modal-actions" style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button type="button" className="btn-secondary" style={{ flex: 1 }} onClick={() => setIsEditModalOpen(false)} disabled={isEditLoading}>
                  Batal
                </button>
                <button type="submit" className="btn-primary" style={{ flex: 1 }} disabled={isEditLoading}>
                  {isEditLoading ? <Loader2 className="spinner" size={16} /> : 'Simpan Perubahan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
