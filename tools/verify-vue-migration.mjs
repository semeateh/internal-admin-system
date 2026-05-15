import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const read = file => fs.readFileSync(path.join(root, file), "utf8");
const exists = file => fs.existsSync(path.join(root, file));
const fail = [];

const requiredFiles = [
  "package.json",
  "src/main.js",
  "src/App.vue",
  "src/data/flow-data.js",
  "src/components/HomeDashboard.vue",
  "src/components/FlowCatalog.vue",
  "src/components/FlowRecords.vue",
  "src/components/TemplateDesigner.vue",
  "src/components/FlowDetail.vue"
];

for (const file of requiredFiles) {
  if (!exists(file)) fail.push(`missing ${file}`);
}

if (exists("index.html")) {
  const html = read("index.html");
  if (!html.includes('id="app"')) fail.push("index.html must expose #app");
  if (html.includes("iframe") || html.includes("reference-release-flow-demo.html")) {
    fail.push("index.html must not iframe the legacy reference page");
  }
  for (const legacy of ["src/scripts/flow-app.js", "src/scripts/flow-data.js", "src/styles/admin.css", "src/styles/flow.css"]) {
    if (html.includes(legacy)) fail.push(`index.html still references ${legacy}`);
  }
}

if (exists("package.json")) {
  const pkg = JSON.parse(read("package.json"));
  if (!pkg.dependencies?.vue?.startsWith("2.")) fail.push("Vue dependency must be Vue 2");
  if (!pkg.dependencies?.["element-ui"]) fail.push("Element UI dependency missing");
}

const vueText = requiredFiles.filter(file => file.endsWith(".vue") && exists(file)).map(read).join("\n");
for (const component of ["el-button", "el-card", "el-tag", "el-input", "el-select", "el-table", "el-tabs", "el-form", "el-pagination"]) {
  if (!vueText.includes(`<${component}`)) fail.push(`missing ${component}`);
}

if (exists("src/data/flow-data.js")) {
  const data = read("src/data/flow-data.js");
  for (const key of ["managementModules", "templates", "instances", "steps", "people", "groups"]) {
    if (!data.includes(key)) fail.push(`data export missing ${key}`);
  }
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Vue migration structure verified");
