import fs from "node:fs";

const layoutSource = fs.readFileSync("src/views/process/ProcessLayout.vue", "utf8");
const detailSource = fs.readFileSync("src/views/process/ProcessDetail.vue", "utf8");

function requireContains(source, snippet, message) {
  if (!source.includes(snippet)) {
    throw new Error(message);
  }
}

requireContains(layoutSource, ":current-user=\"currentUser\"", "ProcessLayout must pass current user into ProcessDetail");
requireContains(detailSource, "currentUser: { type: Object", "FlowDetail must accept currentUser prop");
requireContains(detailSource, "canEditCurrentStep()", "FlowDetail must compute current step edit permission");
requireContains(detailSource, "currentStep.status === \"current\"", "FlowDetail must only allow editing the current step");
requireContains(detailSource, ":disabled=\"fieldLocked\"", "Step fields must be disabled when user cannot edit");
requireContains(detailSource, "taskCanComplete(task)", "Task completion buttons must check task ownership");
requireContains(detailSource, "当前任务没有分配给你", "UI must explain why non-assignees cannot edit");

console.log("Flow detail permissions verified");
