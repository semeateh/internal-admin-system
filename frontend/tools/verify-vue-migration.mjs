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
  "src/router/index.js",
  "src/data/flow-data.js",
  "src/views/dashboard/HomeDashboard.vue",
  "src/views/process/ProcessCatalog.vue",
  "src/views/process/ProcessRecords.vue",
  "src/views/process/ProcessDesigner.vue",
  "src/views/process/ProcessDetail.vue"
];

for (const file of requiredFiles) {
  if (!exists(file)) fail.push(`missing ${file}`);
}

if (exists("index.html")) {
  const html = read("index.html");
  if (!html.includes('id="app"')) fail.push("index.html must expose #app");
}

if (exists("package.json")) {
  const pkg = JSON.parse(read("package.json"));
  for (const dependency of ["vue", "element-ui", "vue-router", "axios"]) {
    if (!pkg.dependencies?.[dependency]) fail.push(`dependency missing ${dependency}`);
  }
}

const vueText = requiredFiles.filter(file => file.endsWith(".vue") && exists(file)).map(read).join("\n");
for (const component of ["el-button", "el-card", "el-tag", "el-input", "el-select", "el-table", "el-tabs", "el-form"]) {
  if (!vueText.includes(`<${component}`)) fail.push(`missing ${component}`);
}

if (fail.length) {
  console.error(fail.join("\n"));
  process.exit(1);
}

console.log("Vue structure verified");
