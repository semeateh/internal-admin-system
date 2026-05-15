import fs from "node:fs";
import path from "node:path";

const frontendRoot = process.cwd();
const repoRoot = path.resolve(frontendRoot, "..");
const readFrontend = file => fs.readFileSync(path.join(frontendRoot, file), "utf8");
const readRepo = file => fs.readFileSync(path.join(repoRoot, file), "utf8");
const existsFrontend = file => fs.existsSync(path.join(frontendRoot, file));
const existsRepo = file => fs.existsSync(path.join(repoRoot, file));
const fail = [];

for (const file of [
  "src/views/login/LoginView.vue",
  "src/api/request.js",
  "src/api/auth.js"
]) {
  if (!existsFrontend(file)) fail.push(`missing ${file}`);
}

for (const file of [
  "backend/app/common/auth.py",
  "backend/app/routes/auth_routes.py",
  "backend/app/routes/template_routes.py",
  "backend/app/routes/instance_routes.py",
  "backend/app/routes/task_routes.py",
  "docs/reference/reference-release-flow-demo.html"
]) {
  if (!existsRepo(file)) fail.push(`missing ${file}`);
}

if (existsRepo("backend/app/common/auth.py")) {
  const auth = readRepo("backend/app/common/auth.py");
  for (const token of ["jwt.encode", "jwt.decode", "bcrypt.checkpw", "def require_auth", "def require_permission", "g.current_user"]) {
    if (!auth.includes(token)) fail.push(`auth.py missing ${token}`);
  }
}

if (existsFrontend("src/api/request.js")) {
  const request = readFrontend("src/api/request.js");
  for (const token of ["axios.create", "Authorization", "Bearer", "setAuthToken", "clearAuthToken", "upload(", "download("]) {
    if (!request.includes(token)) fail.push(`request.js missing ${token}`);
  }
}

if (existsFrontend("src/App.vue")) {
  const appVue = readFrontend("src/App.vue");
  for (const token of ["isAuthenticated", "handleLogin", "handleLogout", "visibleManagementModules"]) {
    if (!appVue.includes(token)) fail.push(`App.vue missing ${token}`);
  }
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Security structure verified");
