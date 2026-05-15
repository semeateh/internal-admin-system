import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.cwd(), "..");
const exists = file => fs.existsSync(path.join(root, file));
const fail = [];

for (const file of [
  "frontend/package.json",
  "frontend/src/router/index.js",
  "frontend/src/api/request.js",
  "frontend/src/views/process/ProcessCatalog.vue",
  "backend/run.py",
  "backend/requirements.txt",
  "backend/app/__init__.py",
  "backend/app/routes/process_routes.py",
  "backend/app/services/process_service.py",
  "backend/app/repositories/process_repository.py",
  "backend/app/models/process.py",
  "backend/app/schemas/process_schema.py",
]) {
  if (!exists(file)) fail.push(`missing ${file}`);
}

if (exists("frontend/package.json")) {
  const pkg = JSON.parse(fs.readFileSync(path.join(root, "frontend/package.json"), "utf8"));
  for (const dependency of ["axios", "vue-router"]) {
    if (!pkg.dependencies?.[dependency]) fail.push(`frontend dependency missing ${dependency}`);
  }
}

if (exists("requirements.txt")) fail.push("root requirements.txt should move under backend/");
if (exists("src")) fail.push("root src/ should move under frontend/");

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Architecture v2 structure verified");
