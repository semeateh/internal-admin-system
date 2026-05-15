import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const read = file => fs.readFileSync(path.join(root, file), "utf8");
const exists = file => fs.existsSync(path.join(root, file));
const fail = [];

const requiredFiles = [
  "backend/app.py",
  "backend/config.py",
  "backend/db.py",
  "backend/routes/auth.py",
  "backend/routes/templates.py",
  "backend/routes/instances.py",
  "backend/routes/tasks.py",
  "backend/services/flow_service.py",
  "backend/migrations/001_fullstack_v1.sql",
  "src/api/request.js",
  "src/api/auth.js",
  "src/api/templates.js",
  "src/api/instances.js"
];

for (const file of requiredFiles) {
  if (!exists(file)) fail.push(`missing ${file}`);
}

if (exists("requirements.txt")) {
  const requirements = read("requirements.txt");
  for (const dependency of ["Flask", "flask-cors", "mysql-connector-python"]) {
    if (!requirements.includes(dependency)) fail.push(`requirements missing ${dependency}`);
  }
}

if (exists("backend/app.py")) {
  const app = read("backend/app.py");
  for (const route of ["auth_bp", "templates_bp", "instances_bp", "tasks_bp"]) {
    if (!app.includes(route)) fail.push(`backend app does not register ${route}`);
  }
}

if (exists("src/App.vue")) {
  const appVue = read("src/App.vue");
  for (const token of ["loadFlowData", "fetchTemplates", "fetchInstances", "createInstance"]) {
    if (!appVue.includes(token)) fail.push(`App.vue missing API integration token ${token}`);
  }
}

if (exists("src/api/request.js")) {
  const request = read("src/api/request.js");
  if (!request.includes("VITE_API_BASE_URL")) fail.push("request.js must support VITE_API_BASE_URL");
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Full-stack v1 structure verified");
