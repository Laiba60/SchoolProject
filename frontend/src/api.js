import axios from 'axios';

// Session + CSRF auth: Django sets the "csrftoken" cookie, Axios echoes it in X-CSRFToken.
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

// DRF lists may be paginated ({results: []}) or plain arrays.
export const rows = (d) => (Array.isArray(d) ? d : d?.results ?? []);

export const GRADES = ['A+', 'A', 'B', 'C', 'D', 'F'];

// One readable line from a DRF error response.
export function errMsg(e) {
  const d = e?.response?.data;
  if (!d) return e?.message === 'Network Error' ? 'Cannot reach the server. Is the backend running?' : e?.message || 'Something went wrong.';
  if (typeof d === 'string') return d.startsWith('<') ? `Server error (${e.response.status}).` : d;
  if (d.detail) return String(d.detail);
  return Object.entries(d)
    .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${[].concat(v).join(' ')}`)
    .join(' | ');
}

// {field: "message"} for showing errors under inputs.
export function fieldErrors(e) {
  const d = e?.response?.data;
  if (!d || typeof d !== 'object' || d.detail) return {};
  return Object.fromEntries(Object.entries(d).map(([k, v]) => [k, [].concat(v).join(' ')]));
}

export default api;
