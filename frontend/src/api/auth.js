import { get, post } from "./request.js";

export function login(payload) {
  return post("/api/auth/login", payload).then(data => data.data || data);
}

export function fetchCurrentUser() {
  return get("/api/auth/me").then(data => data.data || data);
}
