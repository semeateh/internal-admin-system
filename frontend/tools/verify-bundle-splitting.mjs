import fs from "node:fs";
import path from "node:path";

const projectRoot = path.resolve(import.meta.dirname, "..");
const routerPath = path.join(projectRoot, "src", "router", "index.js");
const viteConfigPath = path.join(projectRoot, "vite.config.js");

const routerSource = fs.readFileSync(routerPath, "utf8");
const viteConfigSource = fs.readFileSync(viteConfigPath, "utf8");

const lazyRoutes = [
  "HomeDashboard",
  "LoginView",
  "ProcessLayout",
  "ProcessCatalog",
  "ProcessDesigner",
  "ProcessDetail",
  "ProcessRecords"
];

for (const componentName of lazyRoutes) {
  const lazyImportPattern = new RegExp(
    `const\\s+${componentName}\\s*=\\s*\\(\\)\\s*=>\\s*import\\(`
  );
  if (!lazyImportPattern.test(routerSource)) {
    throw new Error(`${componentName} should be loaded with a dynamic import`);
  }
}

if (!viteConfigSource.includes("manualChunks")) {
  throw new Error("vite config should define manualChunks");
}

if (!viteConfigSource.includes('"base-vendor"')) {
  throw new Error("vite config should define base-vendor chunk");
}

if (!viteConfigSource.includes('"element-ui-vendor"')) {
  throw new Error("vite config should define element-ui-vendor chunk");
}

console.log("Bundle splitting verification passed.");
