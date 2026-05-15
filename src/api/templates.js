import { del, get, post, put } from "./request.js";

function unwrap(data) {
  return data?.data || data;
}

export async function fetchTemplates() {
  const data = await get("/api/flow/templates");
  return data.data?.items || data.items || [];
}

export function createTemplate(payload) {
  return post("/api/flow/templates", payload).then(unwrap);
}

export function fetchTemplate(templateId) {
  return get(`/api/flow/templates/${templateId}`).then(unwrap);
}

export function saveTemplate(templateId, payload) {
  return put(`/api/flow/templates/${templateId}`, payload).then(unwrap);
}

export function createTemplateStep(templateId, payload) {
  return post(`/api/flow/templates/${templateId}/steps`, payload).then(unwrap);
}

export function updateTemplateStep(templateId, stepId, payload) {
  return put(`/api/flow/templates/${templateId}/steps/${stepId}`, payload).then(unwrap);
}

export function deleteTemplateStep(templateId, stepId) {
  return del(`/api/flow/templates/${templateId}/steps/${stepId}`).then(unwrap);
}
