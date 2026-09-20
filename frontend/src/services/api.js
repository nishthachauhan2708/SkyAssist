const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function checkHealth() {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  return res.json();
}

export async function fetchCustomer(pnr) {
  const res = await fetch(`${API_BASE_URL}/api/customers/${pnr}`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchBooking(pnr) {
  const res = await fetch(`${API_BASE_URL}/api/bookings/${pnr}`);
  if (!res.ok) return null;
  return res.json();
}

export async function sendChatMessage(message, pnr = null, customerName = null) {
  const res = await fetch(`${API_BASE_URL}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, pnr, customer_name: customerName }),
  });
  return res.json();
}

export async function executeAction(actionType, pnr, amount = 0, details = '') {
  const endpointMap = {
    refund: '/api/actions/refund',
    rebook: '/api/actions/rebook',
    meal_voucher: '/api/actions/voucher',
    lounge: '/api/actions/lounge',
    hotel: '/api/actions/hotel',
  };
  const url = `${API_BASE_URL}${endpointMap[actionType] || '/api/actions/refund'}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pnr, action_type: actionType, requested_amount: amount, details }),
  });
  return res.json();
}

export async function fetchPolicies(query = '') {
  const res = await fetch(`${API_BASE_URL}/api/policies?query=${encodeURIComponent(query)}`);
  return res.json();
}

export async function fetchAuditLogs(pnr = 'ALL') {
  const res = await fetch(`${API_BASE_URL}/api/audit/${pnr}`);
  return res.json();
}
