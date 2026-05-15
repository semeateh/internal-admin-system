const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";
const TOKEN_KEY = "internal_admin_token";

export function getAuthToken() {
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function setAuthToken(token) {
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new CustomEvent("auth-token-changed"));
}

export function clearAuthToken() {
  setAuthToken("");
}

export async function request(path, options = {}) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    },
    ...options
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken();
      window.dispatchEvent(new CustomEvent("auth-unauthorized"));
    }
    const message = data?.message || `Request failed: ${response.status}`;
    const error = new Error(data?.developerHint ? `${message} ${data.developerHint}` : message);
    error.code = data?.code || `HTTP_${response.status}`;
    error.status = response.status;
    error.developerHint = data?.developerHint || "";
    throw error;
  }
  return data;
}

export function get(path) {
  return request(path);
}

export function post(path, body) {
  return request(path, { method: "POST", body: JSON.stringify(body || {}) });
}

export function put(path, body) {
  return request(path, { method: "PUT", body: JSON.stringify(body || {}) });
}

export function del(path) {
  return request(path, { method: "DELETE" });
}
