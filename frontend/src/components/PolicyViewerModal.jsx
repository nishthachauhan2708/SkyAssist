import React, { useState, useEffect } from 'react';
import { X, BookOpen, ShieldCheck } from 'lucide-react';
import { fetchPolicies } from '../services/api';

export default function PolicyViewerModal({ policyCode, onClose }) {
  const [policies, setPolicies] = useState([]);
  const [selectedCode, setSelectedCode] = useState(policyCode || 'POL-1');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicies('*')
      .then((data) => {
        setPolicies(data || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const currentPolicy = policies.find((p) => p.code === selectedCode) || policies[0];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '1.1rem' }}>
            <BookOpen size={20} className="text-sky-700" />
            <span>Airline Ground Truth Policy KB</span>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '10px', marginBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
          {policies.map((p) => (
            <button
              key={p.code}
              onClick={() => setSelectedCode(p.code)}
              style={{
                background: selectedCode === p.code ? '#0f172a' : '#f1f5f9',
                color: selectedCode === p.code ? '#ffffff' : '#475569',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 12px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              {p.code}: {p.name}
            </button>
          ))}
        </div>

        {loading ? (
          <div>Loading policies...</div>
        ) : currentPolicy ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyBetween: 'space-between', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>{currentPolicy.name}</h3>
              <span className="badge badge-silver" style={{ fontFamily: 'monospace' }}>{currentPolicy.code}</span>
            </div>
            
            <div style={{ backgroundColor: '#f8fafc', padding: '10px 14px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '0.85rem', color: '#334155', marginBottom: '14px', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <ShieldCheck size={16} className="text-emerald-600 mt-0.5 flex-shrink-0" />
              <div>
                <strong>Summary Rule:</strong> {currentPolicy.summary}
              </div>
            </div>

            <div style={{ fontSize: '0.9rem', color: '#1e293b', whiteSpace: 'pre-wrap', lineHeight: '1.6', backgroundColor: '#ffffff', padding: '12px', border: '1px solid #f1f5f9', borderRadius: '6px' }}>
              {currentPolicy.content}
            </div>
          </div>
        ) : (
          <div>Policy details unavailable.</div>
        )}

        <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#0f172a',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
}
