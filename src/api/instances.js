import { get, post, put } from "./request.js";

function unwrap(data) {
  return data?.data || data;
}

export async function fetchInstances(params = {}) {
  const query = params.templateId ? `?templateId=${encodeURIComponent(params.templateId)}` : "";
  const data = await get(`/api/flow/instances${query}`);
  return data.data?.items || data.items || [];
}

export function fetchInstance(instanceId) {
  return get(`/api/flow/instances/${instanceId}`).then(unwrap);
}

export function createInstance(payload) {
  return post("/api/flow/instances", payload).then(unwrap);
}

export function updateInstanceRecord(instanceId, payload) {
  return put(`/api/flow/instances/${instanceId}`, payload).then(unwrap);
}

export function updateInstanceStepFields(instanceId, stepId, values) {
  return put(`/api/flow/instances/${instanceId}/steps/${stepId}/fields`, { values }).then(unwrap);
}

export function completeInstanceTask(instanceId, taskId) {
  return post(`/api/flow/instances/${instanceId}/tasks/${taskId}/complete`).then(unwrap);
}

export function completeInstanceStep(instanceId, stepId) {
  return post(`/api/flow/instances/${instanceId}/steps/${stepId}/complete`).then(unwrap);
}

export function remindInstance(instanceId, message) {
  return post(`/api/flow/instances/${instanceId}/remind`, { message }).then(unwrap);
}
