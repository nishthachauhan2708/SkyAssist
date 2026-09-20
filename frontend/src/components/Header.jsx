import React from 'react';
import { Plane, RotateCcw, ShieldCheck } from 'lucide-react';

export default function Header({ currentPnr, onResetConversation }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="brand-logo">
          <div className="logo-icon-wrapper">
            <Plane className="logo-plane-icon" size={16} />
          </div>
          <div className="brand-text">
            <span className="brand-name">SkyAssist</span>
            <span className="brand-badge">Airline Resolution Desk</span>
          </div>
        </div>
        <span className="header-sub-tag">Customer Disruption Resolution</span>
      </div>

      <div className="header-right">
        <div className="header-case-badge">
          <span className="case-label">CASE</span>
          <span className="case-pnr">{currentPnr}</span>
        </div>

        <div className="header-status">
          <span className="status-dot"></span>
          <span>Agent Online</span>
        </div>

        <button className="reset-conv-btn" onClick={onResetConversation} title="Reset Conversation">
          <RotateCcw size={13} />
          <span>Reset Conversation</span>
        </button>
      </div>
    </header>
  );
}
