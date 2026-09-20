import React from 'react';
import { User, Plane, AlertTriangle, ShieldCheck, CheckCircle } from 'lucide-react';

export default function ScenarioSelector({ selectedPnr, onSelectScenario }) {
  const cases = [
    {
      pnr: 'SK4821X',
      name: 'Priya Nair',
      tier: 'Gold',
      flight: 'SK-204',
      route: 'DEL → GOI',
      status: 'CANCELLED',
      badgeClass: 'badge-cancelled'
    },
    {
      pnr: 'TR1190B',
      name: 'Arvind Kulkarni',
      tier: 'Silver',
      flight: 'SK-118',
      route: 'BOM → BLR',
      status: '4H DELAY',
      badgeClass: 'badge-delayed'
    },
    {
      pnr: 'WL7742',
      name: 'Meher Kaur',
      tier: 'Platinum',
      flight: 'SK-305',
      route: 'DEL → HYD',
      status: '6H DELAY',
      badgeClass: 'badge-delayed'
    }
  ];

  return (
    <aside className="case-queue-sidebar">
      <div className="sidebar-header-box">
        <span className="case-queue-title">CASES QUEUE</span>
        <span className="case-count">3 Active</span>
      </div>

      <div className="case-list">
        {cases.map((c) => {
          const isActive = selectedPnr === c.pnr;
          return (
            <div
              key={c.pnr}
              className={`case-item-card ${isActive ? 'active' : ''}`}
              onClick={() => onSelectScenario(c.pnr)}
            >
              <div className="case-item-top">
                <span className="case-cust-name">{c.name}</span>
                <span className={`tier-tag tier-${c.tier.toLowerCase()}`}>{c.tier}</span>
              </div>

              <div className="case-item-details">
                <span className="case-pnr-text">PNR: {c.pnr}</span>
                <span className="case-flight-text">{c.flight}</span>
              </div>

              <div className="case-item-bottom">
                <span className="case-route">{c.route}</span>
                <span className={`case-status-badge ${c.badgeClass}`}>{c.status}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="case-sidebar-footer">
        <ShieldCheck size={14} className="footer-shield-icon" />
        <div className="footer-brand-mini">
          <span className="footer-title">SkyAssist</span>
          <span className="footer-sub">Resolution Desk</span>
        </div>
      </div>
    </aside>
  );
}
