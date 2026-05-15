import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const read = file => fs.readFileSync(path.join(root, file), "utf8");
const exists = file => fs.existsSync(path.join(root, file));
const fail = [];

const requireFile = file => {
  if (!exists(file)) fail.push(`missing ${file}`);
};

[
  "backend/auth.py",
  "backend/routes/auth.py",
  "backend/routes/templates.py",
  "backend/routes/instances.py",
  "backend/routes/tasks.py",
  "src/components/LoginView.vue",
  "src/api/request.js",
  "src/api/auth.js",
  "docs/reference/reference-release-flow-demo.html"
].forEach(requireFile);

if (exists("src/reference-release-flow-demo.html")) fail.push("legacy reference HTML must be moved out of src");

if (exists("backend/auth.py")) {
  const auth = read("backend/auth.py");
  for (const token of ["jwt.encode", "jwt.decode", "bcrypt.checkpw", "def require_auth", "def require_permission", "g.current_user"]) {
    if (!auth.includes(token)) fail.push(`backend/auth.py missing ${token}`);
  }
}

if (exists("backend/routes/auth.py")) {
  const authRoute = read("backend/routes/auth.py");
  if (authRoute.includes("dev-token")) fail.push("auth route still returns dev-token");
  if (!authRoute.includes("create_token")) fail.push("auth route must issue JWT tokens");
  if (!authRoute.includes("@require_auth")) fail.push("/api/auth/me must require auth");
}

for (const file of ["backend/routes/templates.py", "backend/routes/instances.py", "backend/routes/tasks.py"]) {
  if (!exists(file)) continue;
  const text = read(file);
  if (!text.includes("require_auth") && !text.includes("require_permission")) fail.push(`${file} missing route auth decorators`);
}

if (exists("backend/routes/templates.py")) {
  const text = read("backend/routes/templates.py");
  if (text.includes("501")) fail.push("template write endpoints must be implemented, not return 501");
  for (const token of ["update_template", "add_template_step", "update_template_step", "delete_template_step"]) {
    if (!text.includes(token)) fail.push(`template route missing ${token}`);
  }
}

if (exists("backend/services/flow_service.py")) {
  const service = read("backend/services/flow_service.py");
  for (const token of ["WHERE i.id = %s", "current_step_id", "cursor.rowcount", "assignee_id = %s"]) {
    if (!service.includes(token)) fail.push(`flow_service.py missing safety check token: ${token}`);
  }
  if (service.includes("initiator_id = payload") || service.includes("payload.get(\"initiatorId\")")) {
    fail.push("flow service must not trust payload initiatorId");
  }
}

if (exists("backend/app.py")) {
  const app = read("backend/app.py");
  if (!app.includes("config.APP_ENV") || !app.includes("Internal server error")) fail.push("app error handler must hide prod errors");
}

if (exists("backend/config.py")) {
  const config = read("backend/config.py");
  for (const token of ["JWT_SECRET_KEY", "JWT_ALGORITHM", "JWT_EXPIRE_MINUTES", "validate_security_config"]) {
    if (!config.includes(token)) fail.push(`config missing ${token}`);
  }
}

if (exists("src/api/request.js")) {
  const request = read("src/api/request.js");
  for (const token of ["Authorization", "Bearer", "setAuthToken", "clearAuthToken", "window.dispatchEvent"]) {
    if (!request.includes(token)) fail.push(`request.js missing ${token}`);
  }
}

if (exists("src/App.vue")) {
  const appVue = read("src/App.vue");
  for (const token of ["LoginView", "isAuthenticated", "handleLogin", "handleLogout"]) {
    if (!appVue.includes(token)) fail.push(`App.vue missing ${token}`);
  }
  for (const token of ["hasPermission", "visibleManagementModules", "saveTemplateDesigner"]) {
    if (!appVue.includes(token)) fail.push(`App.vue missing permission/template token: ${token}`);
  }
}

if (exists("src/components/LoginView.vue")) {
  const login = read("src/components/LoginView.vue");
  for (const token of ["el-form", "内部后台管理系统", "apple-login"]) {
    if (!login.includes(token)) fail.push(`LoginView.vue missing ${token}`);
  }
}

if (exists("src/styles/app.css")) {
  const css = read("src/styles/app.css");
  if (!css.includes("backdrop-filter")) fail.push("app.css missing login backdrop-filter styling");
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Security v1 structure verified");
