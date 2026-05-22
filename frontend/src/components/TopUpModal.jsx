import React from 'react';
import { X, CreditCard } from 'lucide-react';
import './TopUpModal.css';

const TopUpModal = ({ isOpen, onClose, instruction }) => {
  if (!isOpen) return null;

  return (
    <div className="topup-modal-overlay animate-fade-in" onClick={onClose}>
      <div className="topup-modal-content glass-panel animate-scale-up" onClick={(e) => e.stopPropagation()}>
        <button className="topup-modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>
        
        <div className="topup-modal-header">
          <div className="topup-modal-icon-container">
            <CreditCard size={24} className="topup-modal-icon" />
          </div>
          <div>
            <h3>TopUp Saldo Kredit</h3>
            <p>Tambah token untuk memotong klip viral Anda</p>
          </div>
        </div>

        <div className="topup-modal-body">
          <div className="topup-instruction-box">
            <p className="instruction-text">{instruction || "Memuat instruksi..."}</p>
          </div>
          
          <div className="topup-info-badge">
            <span className="info-icon">💡</span>
            <span className="info-text">Kredit akan ditambahkan oleh Admin secara manual setelah pembayaran dikonfirmasi via WhatsApp.</span>
          </div>
        </div>

        <div className="topup-modal-footer">
          <button className="btn-primary full-width" onClick={onClose}>
            Saya Mengerti
          </button>
        </div>
      </div>
    </div>
  );
};

export default TopUpModal;
