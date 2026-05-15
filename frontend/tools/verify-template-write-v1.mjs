import fs from "node:fs";
import path from "node:path";

const frontendRoot = process.cwd();
const repoRoot = path.resolve(frontendRoot, "..");
const readFrontend = file => fs.readFileSync(path.join(frontendRoot, file), "utf8");
const readRepo = file => fs.readFileSync(path.join(repoRoot, file), "utf8");
const fail = [];

for (const [root, file] of [
  [repoRoot, "backend/app/routes/template_routes.py"],
  [repoRoot, "backend/app/services/process_service.py"],
  [repoRoot, "backend/app/common/responses.py"],
  [frontendRoot, "src/api/templates.js"],
  [frontendRoot, "src/api/request.js"],
  [frontendRoot, "src/views/process/ProcessLayout.vue"],
  [frontendRoot, "src/views/process/ProcessDesigner.vue"],
  [frontendRoot, "src/views/process/ProcessCatalog.vue"]
]) {
  if (!fs.existsSync(path.join(root, file))) fail.push(`missing ${file}`);
}

if (!fail.length) {
  const routes = readRepo("backend/app/routes/template_routes.py");
  for (const token of ["create_template", "update_template", "add_template_step", "update_template_step", "delete_template_step"]) {
    if (!routes.includes(token)) fail.push(`template routes missing ${token}`);
  }

  const service = readRepo("backend/app/services/process_service.py");
  for (const token of ["def create_template", "def update_template", "flow_template_step_fields", "flow_template_step_assignees", "operation_logs"]) {
    if (!service.includes(token)) fail.push(`process service missing ${token}`);
  }

  const api = readFrontend("src/api/templates.js");
  for (const token of ["createTemplate", "saveTemplate", "createTemplateStep", "updateTemplateStep", "deleteTemplateStep"]) {
    if (!api.includes(token)) fail.push(`templates api missing ${token}`);
  }

  const layout = readFrontend("src/views/process/ProcessLayout.vue");
  for (const token of ["createFlowTemplate", "saveTemplateDesigner", "flow.template.manage", "flow.instance.start"]) {
    if (!layout.includes(token)) fail.push(`ProcessLayout missing ${token}`);
  }
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Template write structure verified");
