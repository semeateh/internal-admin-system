import axios from "axios";

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

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

client.interceptors.request.use(config => {
  const token = getAuthToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status || 0;
    const data = error.response?.data || {};
    if (status === 401) {
      clearAuthToken();
      window.dispatchEvent(new CustomEvent("auth-unauthorized"));
    }
    const message = data?.message || error.message || `Request failed: ${status}`;
    const normalized = new Error(data?.developerHint ? `${message} ${data.developerHint}` : message);
    normalized.code = data?.code || (status ? `HTTP_${status}` : "NETWORK_ERROR");
    normalized.status = status;
    normalized.developerHint = data?.developerHint || "";
    throw normalized;
  }
);

export function request(config) {
  return client(config);
}

export function get(path, config = {}) {
  return request({ url: path, method: "GET", ...config });
}

export function post(path, body, config = {}) {
  return request({ url: path, method: "POST", data: body || {}, ...config });
}

export function put(path, body, config = {}) {
  return request({ url: path, method: "PUT", data: body || {}, ...config });
}

export function del(path, config = {}) {
  return request({ url: path, method: "DELETE", ...config });
}

export function upload(path, formData, { onUploadProgress, ...config } = {}) {
  return request({
    url: path,
    method: "POST",
    data: formData,
    headers: { "Content-Type": "multipart/form-data", ...(config.headers || {}) },
    onUploadProgress,
    ...config
  });
}

export function download(path, config = {}) {
  return request({
    url: path,
    method: "GET",
    responseType: "blob",
    ...config
  });
}
