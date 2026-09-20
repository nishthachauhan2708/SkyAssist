import React from 'react';
import { User, Plane, FileText, Activity, ShieldCheck, ArrowRight, ExternalLink, AlertCircle, CheckCircle, Clock } from 'lucide-react';

export default function CustomerPanel({ customer, booking, entitlements, policySource, auditLogs, onViewPolicy }) {
  if (!customer || !booking) {
    return (
      <aside className="sidebar-section">
        <div className="sidebar-placeholder">
          Select an assessment scenario to view operations context.
        </div>
      </aside>
    );
  }

  const getBadgeClass = (tier) => {
    if (tier === 'Gold') return 'badge-gold';
    if (tier === 'Silver') return 'badge-silver';
    if (tier === 'Platinum') return 'badge-platinum';
    return 'badge-silver';
  };

  const getStatusBadge = (status) => {
    if (status.includes('CANCEL')) return 'badge-cancelled';
    if (status.includes('Delayed') || status.includes('DELAY')) return 'badge-delayed';
    return 'badge-ok';
  };

  const isCancelled = booking.status.includes('CANCEL');
  const is4hDelay = booking.status.includes('4');
  const is6hDelay = booking.status.includes('6');

  // Grounded resolution status calculation
  let refundStatus = isCancelled ? 'Available / Initiated' : 'Not Applicable';
  let rebookingStatus = isCancelled ? 'Available (Free 24h)' : 'Standard Flight';
  let priorityText = `${customer.loyalty_tier} Priority`;

  return (
    <aside className="sidebar-section">
      <div className="panel-main-title">OPERATIONS CONTEXT</div>

      {/* 1. TRIP OVERVIEW */}
      <div className="sidebar-group">
        <div className="section-label">
          <Plane size={13} />
          <span>TRIP OVERVIEW</span>
        </div>
        <div className="info-card">
          <div className="card-header-row">
            <div>
              <div className="cust-name">{customer.name}</div>
              <div className="pnr-code">PNR: {customer.booking_reference}</div>
            </div>
            <span className={`badge ${getBadgeClass(customer.loyalty_tier)}`}>
              {customer.loyalty_tier} Member
            </span>
          </div>

          <div className="mini-route-box">
            <div className="mini-route-cities">
              <span className="mini-city">{booking.origin}</span>
              <ArrowRight size={14} className="mini-arrow" />
              <span className="mini-city">{booking.destination}</span>
            </div>
            <div className="mini-flight-meta">
              <span>{booking.flight_number}</span>
              <span>•</span>
              <span>23 Sep 2026 · {booking.scheduled_departure}</span>
            </div>
          </div>

          <div className="card-row font-sm">
            <span className="card-label">Status:</span>
            <span className={`badge ${getStatusBadge(booking.status)}`}>
              {booking.status}
            </span>
          </div>
          {booking.reason && (
            <div className="card-row font-xs">
              <span className="card-label">Reason:</span>
              <span className="card-value-sub">{booking.reason}</span>
            </div>
          )}
        </div>
      </div>

      {/* 2. RESOLUTION STATUS */}
      <div className="sidebar-group">
        <div className="section-label">
          <CheckCircle size={13} />
          <span>RESOLUTION STATUS</span>
        </div>
        <div className="info-card resolution-status-box">
          <div className="res-row">
            <span className="res-label">Refund</span>
            <span className="res-value font-semibold">{refundStatus}</span>
          </div>
          <div className="res-row">
            <span className="res-label">Rebooking</span>
            <span className="res-value font-semibold">{rebookingStatus}</span>
          </div>
          <div className="res-row">
            <span className="res-label">Priority</span>
            <span className="res-value font-semibold text-sky">{priorityText}</span>
          </div>
        </div>
      </div>

      {/* 3. ENTITLEMENTS */}
      {entitlements && (
        <div className="sidebar-group">
          <div className="section-label">
            <ShieldCheck size={13} />
            <span>ENTITLEMENTS</span>
          </div>
          <div className="entitlements-grid">
            <div className="entitlement-item">
              <span className="ent-label">Meal Voucher</span>
              <span className={`ent-val ${entitlements.meal_voucher_eligible ? 'eligible' : 'ineligible'}`}>
                {entitlements.meal_voucher_eligible ? `₹${entitlements.meal_voucher_amount}` : 'Not Eligible'}
              </span>
            </div>

            <div className="entitlement-item">
              <span className="ent-label">Lounge</span>
              <span className={`ent-val ${entitlements.lounge_access_eligible ? 'eligible' : 'ineligible'}`}>
                {entitlements.lounge_access_eligible ? 'Eligible' : 'Not Eligible'}
              </span>
            </div>

            <div className="entitlement-item col-span-2">
              <span className="ent-label">Hotel</span>
              <span className={`ent-val ${entitlements.hotel_eligible ? 'eligible' : 'ineligible'}`}>
                {entitlements.hotel_eligible
                  ? 'Delayed Hours Only'
                  : (isCancelled ? 'Not applicable for cancellation' : 'Ineligible (<5h delay)')}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 4. POLICY CONTEXT */}
      <div className="sidebar-group">
        <div className="section-label">
          <FileText size={13} />
          <span>POLICY CONTEXT</span>
        </div>
        <div className="policy-context-list">
          <div className="policy-badge-row">
            <button className="pol-chip" onClick={() => onViewPolicy('POL-1')} title="Cancellation Policy">
              POL-1 (Cancellation)
            </button>
            <button className="pol-chip" onClick={() => onViewPolicy('POL-2')} title="Delay Compensation">
              POL-2 (Delay)
            </button>
            <button className="pol-chip" onClick={() => onViewPolicy('POL-3')} title="Refund Processing">
              POL-3 (Refund)
            </button>
            <button className="pol-chip" onClick={() => onViewPolicy('POL-4')} title="Fare Waiver">
              POL-4 (Waiver)
            </button>
            <button className="pol-chip" onClick={() => onViewPolicy('POL-5')} title="Loyalty Perks">
              POL-5 (Loyalty)
            </button>
          </div>

          <div className="active-policy-summary">
            <div className="active-pol-header">
              <span className="active-pol-code">{policySource?.policy_code || 'POL-1'}</span>
              <span className="active-pol-name">{policySource?.policy_name || 'Cancellation Rebooking & Refund'}</span>
            </div>
            <div className="active-pol-desc">
              {policySource?.decision || 'Free rebooking on next available flight within 24h OR full refund.'}
            </div>
            <button className="view-policy-btn" onClick={() => onViewPolicy(policySource?.policy_code || 'POL-1')}>
              <span>View full policy rule</span>
              <ExternalLink size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* 5. CASE ACTIVITY */}
      <div className="sidebar-group">
        <div className="section-label">
          <Activity size={13} />
          <span>CASE ACTIVITY</span>
        </div>
        <div className="activity-list">
          {auditLogs && auditLogs.length > 0 ? (
            auditLogs.map((log, lIdx) => (
              <div key={lIdx} className="activity-item">
                <div className="activity-time font-mono">{log.timestamp}</div>
                <div className="activity-event">{log.event}</div>
              </div>
            ))
          ) : (
            <div className="activity-empty">No activity recorded yet.</div>
          )}
        </div>
      </div>
    </aside>
  );
}
