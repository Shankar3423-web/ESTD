import React from 'react';
import { X, Folder, FolderTree } from 'lucide-react';

export default function DriveHierarchyModal({ isOpen, onClose, driveData = {} }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <FolderTree size={20} className="text-blue-400" />
            Google Drive Verified Hierarchy
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>
          Google Documents created by Step 8 are deterministically routed to category folders:
        </p>

        <div className="tree-view">
          My Drive<br />
          └── <strong style={{ color: '#fff' }}>ESTD CONTENT</strong> (Root Folder)<br />
          &nbsp;&nbsp;&nbsp;&nbsp;├── Entertainment (Hollywood, Bollywood, Regional Cinema, Streaming...)<br />
          &nbsp;&nbsp;&nbsp;&nbsp;├── Sports (Cricket, Football, Tennis, Formula 1, Esports...)<br />
          &nbsp;&nbsp;&nbsp;&nbsp;├── Tech (AI & ML, Big Tech, Mobile, Cybersecurity, Cloud...)<br />
          &nbsp;&nbsp;&nbsp;&nbsp;├── Developments (Scientific Breakthroughs, Space, Clean Energy, Policy...)<br />
          &nbsp;&nbsp;&nbsp;&nbsp;└── Business & Finance (Markets, Economy, Venture Capital, Fintech...)
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--text-secondary)', marginTop: 12 }}>
          <span>Documents Created: <strong style={{ color: '#34d399' }}>{driveData.documents_created ?? 0}</strong></span>
          <span>Documents Failed: <strong style={{ color: driveData.documents_failed ? '#f87171' : '#94a3b8' }}>{driveData.documents_failed ?? 0}</strong></span>
        </div>

        <div style={{ textAlign: 'right', marginTop: 20 }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
