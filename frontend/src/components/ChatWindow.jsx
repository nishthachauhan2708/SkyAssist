import React, { useState, useEffect, useRef } from 'react';
import { Send, CheckCircle2, ShieldAlert, Plane, Clock, Shield, ArrowRight, Activity, AlertCircle, FileCheck, Layers } from 'lucide-react';

export default function ChatWindow({ booking, messages, onSendMessage, isThinking, promptChips = [] }) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isThinking) return;
    onSendMessage(inputText);
    setInputText('');
  };

  const handleChipClick = (chipText) => {
    if (isThinking) return;
    onSendMessage(chipText);
  };

  // Derive Live Case Status values dynamically from booking
  const pnr = booking?.pnr || 'SK4821X';
  const disruptionStatus = booking?.status || 'CANCELLED';
  const isEscalated = messages.some(m => m.escalated);
  const hasAction = messages.some(m => m.actionsTaken && m.actionsTaken.length > 0);
  
  const resolutionStatus = hasAction || isEscalated ? 'IN PROGRESS / PARTIAL' : 'ACTIVE';
  const authorityText = isEscalated ? 'AUTONOMOUS + SUPERVISOR ESCALATION' : 'AUTONOMOUS AGENT AUTHORITY';

  const getDisruptionBadgeStyle = (status) => {
    if (status.includes('CANCEL')) return 'disruption-cancelled';
    if (status.includes('Delayed')) return 'disruption-delayed';
    return 'disruption-normal';
  };

  return (
    <div className="chat-section">
      {/* 1. Live Case Status Strip */}
      <div className="case-status-strip">
        <div className="strip-item">
          <span className="strip-label">CASE</span>
          <span className="strip-val font-mono">{pnr}</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">DISRUPTION</span>
          <span className={`strip-val-badge ${getDisruptionBadgeStyle(disruptionStatus)}`}>
            {disruptionStatus}
          </span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">RESOLUTION</span>
          <span className="strip-val">{resolutionStatus}</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item hide-mobile">
          <span className="strip-label">AUTHORITY</span>
          <span className="strip-val authority-val">{authorityText}</span>
        </div>
      </div>

      {/* 2. Flight Header & Visual Route Display */}
      {booking && (
        <div className="flight-route-banner">
          <div className="route-banner-info">
            <span className="banner-flight-num">{booking.flight_number}</span>
            <span className="banner-flight-date">{booking.departure_date || '23 Sep 2026'}</span>
          </div>

          <div className="visual-route-line">
            <span className="route-city-code">{booking.origin}</span>
            <div className="route-line-graphic">
              <div className="line-segment" />
              <Plane size={14} className="route-plane-icon" />
              <div className="line-segment" />
            </div>
            <span className="route-city-code">{booking.destination}</span>
          </div>

          <div className="route-banner-time">
            <span className="time-scheduled">Sched: {booking.scheduled_departure}</span>
            {booking.new_departure && (
              <span className="time-new">New: {booking.new_departure}</span>
            )}
          </div>
        </div>
      )}

      {/* 3. Resolution Workflow Timeline */}
      <div className="workflow-timeline-bar">
        <div className="workflow-step completed">
          <FileCheck size={12} />
          <span>BOOKING</span>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step active">
          <AlertCircle size={12} />
          <span>DISRUPTION</span>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step active">
          <Shield size={12} />
          <span>ELIGIBILITY</span>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step active">
          <Activity size={12} />
          <span>RESOLUTION</span>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step">
          <Layers size={12} />
          <span>AUDIT</span>
        </div>
      </div>

      {/* 4. Chat Messages List */}
      <div className="chat-messages">
        {messages.map((msg, idx) => {
          const isUser = msg.sender === 'user';
          return (
            <div key={idx} className={`message-item ${isUser ? 'user' : 'agent'}`}>
              <div className={`avatar ${isUser ? 'user-avatar' : 'agent-avatar'}`}>
                {isUser ? 'CUST' : 'SA'}
              </div>
              <div className="message-content">
                <div className="sender-name-label">
                  {isUser ? 'Customer' : 'SkyAssist Resolution Agent'}
                </div>

                <div className="message-bubble">
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                  
                  {/* Compact Action Result Cards */}
                  {msg.actionsTaken && msg.actionsTaken.length > 0 && (
                    <div className="action-cards-container">
                      {msg.actionsTaken.map((act, aIdx) => (
                        <div 
                          key={aIdx} 
                          className={`compact-action-card ${act.success ? 'success' : 'escalated'}`}
                        >
                          <div className="compact-action-header">
                            <span className="compact-action-title">
                              {act.success ? (
                                <CheckCircle2 size={13} className="text-success flex-shrink-0" />
                              ) : (
                                <ShieldAlert size={13} className="text-escalated flex-shrink-0" />
                              )}
                              <span>{act.action ? act.action.replace('_', ' ').toUpperCase() : (act.success ? 'ACTION EXECUTED' : 'ESCALATED TO SUPERVISOR')}</span>
                            </span>
                            <span className="compact-action-id">
                              {act.action_id || act.escalation_id}
                            </span>
                          </div>
                          <div className="compact-action-details">{act.details || act.reason}</div>
                          {act.policy_source && (
                            <div className="compact-action-policy">{act.policy_source}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.escalated && (!msg.actionsTaken || msg.actionsTaken.length === 0) && (
                    <div className="action-cards-container">
                      <div className="compact-action-card escalated">
                        <div className="compact-action-header">
                          <span className="compact-action-title">
                            <ShieldAlert size={13} className="text-escalated flex-shrink-0" />
                            <span>ESCALATED TO SUPERVISOR</span>
                          </span>
                          <span className="compact-action-id">{msg.escalation_id || 'ESC-ALERT'}</span>
                        </div>
                        <div className="compact-action-details">Request sent to passenger relations supervisor for manual authority approval.</div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="message-time">{msg.timestamp}</div>
              </div>
            </div>
          );
        })}

        {isThinking && (
          <div className="message-item agent">
            <div className="avatar agent-avatar">SA</div>
            <div className="message-content">
              <div className="sender-name-label">SkyAssist Resolution Agent</div>
              <div className="message-bubble thinking-bubble">
                Checking policy rules & authority thresholds...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 5. Input Section */}
      <div className="chat-input-container">
        {promptChips && promptChips.length > 0 && (
          <div className="quick-prompts">
            <span className="chips-label">Quick Queries:</span>
            {promptChips.map((chip, cIdx) => (
              <button key={cIdx} className="prompt-chip" onClick={() => handleChipClick(chip)}>
                {chip}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-row">
          <input
            type="text"
            className="chat-input"
            placeholder="Type customer or policy query..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isThinking}
          />
          <button type="submit" className="send-btn" disabled={isThinking || !inputText.trim()}>
            <span>Submit</span>
            <Send size={14} />
          </button>
        </form>
      </div>
    </div>
  );
}
