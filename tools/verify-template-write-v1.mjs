import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const read = file => fs.readFileSync(path.join(root, file), "utf8");
const fail = [];

const files = [
  "backend/routes/templates.py",
  "backend/services/flow_service.py",
  "backend/responses.py",
  "src/api/templates.js",
  "src/api/request.js",
  "src/App.vue",
  "src/components/TemplateDesigner.vue",
  "src/components/FlowCatalog.vue"
];

for (const file of files) {
  if (!fs.existsSync(path.join(root, file))) fail.push(`missing ${file}`);
}

if (!fail.length) {
  const routes = read("backend/routes/templates.py");
  if (routes.includes("501")) fail.push("template write routes still return 501");
  for (const token of ["api_success", "create_template", "update_template", "add_template_step", "update_template_step", "delete_template_step"]) {
    if (!routes.includes(token)) fail.push(`template routes missing ${token}`);
  }

  const service = read("backend/services/flow_service.py");
  for (const token of [
    "def create_template",
    "def update_template",
    "def add_template_step",
    "def update_template_step",
    "def delete_template_step",
    "flow_template_step_fields",
    "flow_template_step_assignees",
    "cursor.rowcount",
    "operation_logs"
  ]) {
    if (!service.includes(token)) fail.push(`flow service missing ${token}`);
  }

  const api = read("src/api/templates.js");
  for (const token of ["createTemplate", "saveTemplate", "createTemplateStep", "updateTemplateStep", "deleteTemplateStep", "unwrap"]) {
    if (!api.includes(token)) fail.push(`templates api missing ${token}`);
  }

  const request = read("src/api/request.js");
  for (const token of ["error.code", "developerHint", "DELETE"]) {
    if (!request.includes(token)) fail.push(`request api missing ${token}`);
  }

  const app = read("src/App.vue");
  for (const token of ["hasPermission", "visibleManagementModules", "createFlowTemplate", "saveTemplateDesigner", "flow.template.manage", "flow.instance.start"]) {
    if (!app.includes(token)) fail.push(`App.vue missing ${token}`);
  }

  const designer = read("src/components/TemplateDesigner.vue");
  for (const token of ["buildPayload", "deletedStepIds", "stepNo", "assignees"]) {
    if (!designer.includes(token)) fail.push(`TemplateDesigner missing ${token}`);
  }

  const catalog = read("src/components/FlowCatalog.vue");
  if (!catalog.includes("canManageTemplate")) fail.push("FlowCatalog must hide template config action without permission");
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Template write v1 structure verified");
