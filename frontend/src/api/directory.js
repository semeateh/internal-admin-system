import { get } from "./request.js";

export function fetchPeopleDirectory() {
  return get("/api/directory/people").then(data => data?.data || data);
}
