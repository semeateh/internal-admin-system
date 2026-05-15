import fs from "node:fs";
import path from "node:path";

const backendRoot = process.cwd();
const repoRoot = path.resolve(backendRoot, "..");
const read = file => fs.readFileSync(path.join(repoRoot, file), "utf8");
const exists = file => fs.existsSync(path.join(repoRoot, file));
const fail = [];

for (const file of [
  "backend/run.py",
  "backend/app/__init__.py",
  "backend/app/config.py",
  "backend/app/db.py",
  "backend/app/routes/process_routes.py",
  "backend/app/services/process_service.py",
  "backend/app/repositories/process_repository.py",
  "backend/app/models/process.py",
  "backend/app/schemas/process_schema.py",
  "backend/migrations/001_fullstack_v1.sql",
  "frontend/src/api/request.js",
  "frontend/src/api/auth.js",
  "frontend/src/api/templates.js",
  "frontend/src/api/instances.js"
]) {
  if (!exists(file)) fail.push(`missing ${file}`);
}

if (exists("backend/requirements.txt")) {
  const requirements = read("backend/requirements.txt");
  for (const dependency of ["Flask", "flask-cors", "mysql-connector-python"]) {
    if (!requirements.includes(dependency)) fail.push(`requirements missing ${dependency}`);
  }
}

if (exists("backend/app/__init__.py")) {
  const app = read("backend/app/__init__.py");
  for (const route of ["auth_bp", "directory_bp", "process_blueprints"]) {
    if (!app.includes(route)) fail.push(`backend app does not register ${route}`);
  }
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Full-stack structure verified");
