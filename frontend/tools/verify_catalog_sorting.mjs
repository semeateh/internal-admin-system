import fs from "node:fs";

const source = fs.readFileSync("src/views/process/ProcessCatalog.vue", "utf8");

function requireContains(snippet, message) {
  if (!source.includes(snippet)) {
    throw new Error(message);
  }
}

requireContains('new Intl.Collator("zh-Hans-CN"', "department sorting must use zh-Hans-CN Intl.Collator");
requireContains("sortedDepartments()", "department list must be built through sortedDepartments()");
requireContains("return [ALL_DEPARTMENTS, ...names]", "All departments option must stay first");
requireContains("sortedFilteredTemplates()", "template rendering must use sortedFilteredTemplates()");
requireContains("getTemplateUpdatedTime", "template sorting must use updated time");

console.log("Catalog sorting verified");
