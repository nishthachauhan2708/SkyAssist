import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ScenarioSelector from './components/ScenarioSelector';
import ChatWindow from './components/ChatWindow';
import CustomerPanel from './components/CustomerPanel';
import PolicyViewerModal from './components/PolicyViewerModal';
import { fetchCustomer, fetchBooking, sendChatMessage, fetchAuditLogs } from './services/api';

export default function App() {
  const [currentPnr, setCurrentPnr] = useState('SK4821X');
  const [customer, setCustomer] = useState(null);
  const [booking, setBooking] = useState(null);
  const [entitlements, setEntitlements] = useState(null);
  const [policySource, setPolicySource] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [modalPolicyCode, setModalPolicyCode] = useState(null);

  // Scenario prompt chips tailored per case
  const promptChipsMap = {
    SK4821X: [
      'I am furious about SK-204 being cancelled. I want a full refund and a free business class upgrade on my return flight!',
      'Check my flight',
      'Check delay',
      'What is my PNR?',
      'Refund options',
      'Rebooking options',
      'What is the fare difference policy?'
    ],
    TR1190B: [
      'My flight SK-118 is delayed by 4 hours. I want hotel accommodation for my delay.',
      'Check my flight',
      'Check delay',
      'Meal & lounge',
      'Hotel eligibility',
      'What happens if delay is >5h?',
      'Refund options',
      'Rebooking options',
      'What is the fare difference policy?',
      'What is my PNR?'
    ],
    WL7742: [
      'My flight SK-305 is delayed by 6 hours. I want full-night hotel stay and a ₹2,000 fare difference waiver.',
      'Check my flight',
      'Check delay',
      'Meal & lounge',
      'Hotel eligibility',
      'What happens if delay is >5h?',
      'Refund options',
      'Rebooking options',
      'Waive ₹2,000 fare difference',
      'What is the fare difference policy?',
      'What is my PNR?'
    ]
  };

  const loadScenarioData = async (pnr) => {
    try {
      const custData = await fetchCustomer(pnr);
      const bookData = await fetchBooking(pnr);
      const logsData = await fetchAuditLogs(pnr);

      setCustomer(custData);
      if (bookData) {
        setBooking(bookData.booking);
        setEntitlements(bookData.entitlements);
      }
      setAuditLogs(logsData || []);

      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const firstName = custData?.name ? custData.name.split(' ')[0] : 'there';
      const initialReply = `Hello ${firstName}! I'm SkyAssist, your airline support agent. How can I help you today?`;

      setMessages([
        {
          sender: 'agent',
          text: initialReply,
          timestamp: nowStr
        }
      ]);
    } catch (err) {
      console.error('Error loading scenario:', err);
    }
  };

  useEffect(() => {
    loadScenarioData(currentPnr);
  }, [currentPnr]);

  const handleSelectScenario = (pnr) => {
    setCurrentPnr(pnr);
  };

  const handleResetConversation = () => {
    loadScenarioData(currentPnr);
  };

  const handleSendMessage = async (text) => {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newMsgList = [...messages, { sender: 'user', text, timestamp: timeStr }];
    setMessages(newMsgList);
    setIsThinking(true);

    try {
      const res = await sendChatMessage(text, currentPnr, customer?.name);
      setIsThinking(false);

      const agentTimeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: res.reply,
          timestamp: agentTimeStr,
          actionsTaken: res.actions_taken || [],
          escalated: res.escalated,
          escalation_id: res.escalation_id
        }
      ]);

      if (res.source_policy) {
        setPolicySource(res.source_policy);
      }

      // Refresh Audit logs & Booking details
      const freshLogs = await fetchAuditLogs(currentPnr);
      setAuditLogs(freshLogs || []);

      const freshBook = await fetchBooking(currentPnr);
      if (freshBook) {
        setBooking(freshBook.booking);
        setEntitlements(freshBook.entitlements);
      }
    } catch (err) {
      setIsThinking(false);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: 'I encountered an error connecting to the resolution engine. Please check backend API server.',
          timestamp: timeStr
        }
      ]);
    }
  };

  return (
    <div className="app-container">
      <Header currentPnr={currentPnr} onResetConversation={handleResetConversation} />

      <div className="main-workspace">
        <ScenarioSelector selectedPnr={currentPnr} onSelectScenario={handleSelectScenario} />

        <ChatWindow
          booking={booking}
          messages={messages}
          onSendMessage={handleSendMessage}
          isThinking={isThinking}
          promptChips={promptChipsMap[currentPnr] || []}
        />

        <CustomerPanel
          customer={customer}
          booking={booking}
          entitlements={entitlements}
          policySource={policySource}
          auditLogs={auditLogs}
          onViewPolicy={(code) => setModalPolicyCode(code)}
        />
      </div>

      <footer className="app-footer">
        <span>✈ SkyAssist Operations Console</span>
        <span className="footer-dot">•</span>
        <span>Policy-Grounded Airline Disruption Engine</span>
        <span className="footer-dot">•</span>
        <span>AIONOS Autonomous Resolution Systems</span>
      </footer>

      {modalPolicyCode && (
        <PolicyViewerModal
          policyCode={modalPolicyCode}
          onClose={() => setModalPolicyCode(null)}
        />
      )}
    </div>
  );
}
