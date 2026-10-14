/* Backend API client. The existing demo stays unchanged until individual flows migrate. */
const API_BASE_URL = (window.TRAIN_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

async function trainApiRequest(path, { method = 'GET', body, token } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  } catch {
    throw new Error('Cannot connect to the train booking server. Please check that the backend is running.');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string' ? detail : 'The request could not be completed.';
    throw new Error(message);
  }
  return data;
}

const trainApi = Object.freeze({
  health: () => trainApiRequest('/api/health'),
  stations: () => trainApiRequest('/api/stations'),
  trains: () => trainApiRequest('/api/trains'),
  schedules: () => trainApiRequest('/api/schedules'),
  search: ({ originStationId, destinationStationId, travelDate, preferredTime }) => {
    const query = new URLSearchParams({
      origin_station_id: String(originStationId),
      destination_station_id: String(destinationStationId),
    });
    if (travelDate) query.set('travel_date', travelDate);
    if (preferredTime) query.set('preferred_time', preferredTime);
    return trainApiRequest(`/api/trains/search?${query}`);
  },
  register: payload => trainApiRequest('/api/auth/register', { method: 'POST', body: payload }),
  login: payload => trainApiRequest('/api/auth/login', { method: 'POST', body: payload }),
  me: token => trainApiRequest('/api/users/me', { token }),
  myBookings: token => trainApiRequest('/api/bookings/mine', { token }),
  wallet: token => trainApiRequest('/api/wallet', { token }),
  transactions: token => trainApiRequest('/api/wallet/transactions', { token }),
  myReports: token => trainApiRequest('/api/reports/mine', { token }),
  adminDashboard: token => trainApiRequest('/api/admin/dashboard', { token }),
});
