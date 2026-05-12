(function () {
  const data = window.FlowSeedData;
  const state = {
    module: "home",
    view: "catalog",
    selectedDepartment: "全部",
    selectedTemplateId: "release-market-sales",
    selectedInstanceId: "inst-1",
    recordTab: "active",
    page: 1,
    pageSize: 9,
    activeStep: 0,
    steps: data.steps.map(item => ({ ...item })),
    cloudPath: "\\\\server\\市场销售部\\产品Release\\Semea X1"
  };

  const el = id => document.getElementById(id);
  const moduleInfo = module => data.managementModules.find(item => item.id === module);
  const template = () => data.templates.find(item => item.id === state.selectedTemplateId) || data.templates[0];
  const instance = () => data.instances.find(item => item.id === state.selectedInstanceId) || data.instances[0];

  function toast(message) {
    el("toast").textContent = message;
    el("toast").classList.remove("hidden");
    window.clearTimeout(window.__toastTimer);
    window.__toastTimer = window.setTimeout(() => el("toast").classList.add("hidden"), 1800);
  }

  function showModule(module) {
    state.module = module;
    el("homeNav").classList.toggle("active", module === "home");
    el("manageNav").classList.toggle("active", module !== "home");
    document.querySelectorAll(".nav-menu-item").forEach(button => button.classList.toggle("active", button.dataset.module === module));
    el("pageTop").classList.toggle("hidden", module === "home" || module === "flow");
    el("homeView").classList.toggle("hidden", module !== "home");
    el("flowReferenceView").classList.toggle("hidden", module !== "flow");
    el("flowCatalog").classList.add("hidden");
    el("recordsView").classList.add("hidden");
    el("detailView").classList.add("hidden");
    el("placeholderModule").classList.toggle("hidden", module === "home" || module === "flow");
    el("createTemplateBtn").classList.add("hidden");
    if (module !== "home" && module !== "flow") {
      el("placeholderTitle").textContent = moduleInfo(module)?.title || "模块建设中";
    }
    renderBreadcrumb();
  }

  function setFlowView(view) {
    state.module = "flow";
    state.view = view;
    showModule("flow");
  }

  function renderBreadcrumb() {
    let crumbs = [];
    if (state.module === "home") {
      crumbs = [{ label: "首页" }];
    } else if (state.module !== "flow") {
      crumbs = [{ label: "首页", action: "home" }, { label: moduleInfo(state.module)?.title || "内部后台" }];
    } else if (state.view === "catalog") {
      crumbs = [{ label: "首页", action: "home" }, { label: "流程管理" }];
    } else {
      crumbs = [{ label: "首页", action: "home" }, { label: "流程管理", action: "catalog" }, { label: template().name, action: state.view === "detail" ? "records" : "" }];
      if (state.view === "detail") crumbs.push({ label: instance().name });
    }
    el("breadcrumb").innerHTML = crumbs.map((crumb, index) => {
      const item = crumb.action ? `<button type="button" data-crumb="${crumb.action}">${crumb.label}</button>` : `<strong>${crumb.label}</strong>`;
      return index === 0 ? item : `<span class="crumb-separator">></span>${item}`;
    }).join("");
    el("breadcrumb").querySelectorAll("[data-crumb]").forEach(button => {
      button.addEventListener("click", () => {
        if (button.dataset.crumb === "home") { showModule("home"); renderHome(); }
        if (button.dataset.crumb === "catalog") { setFlowView("catalog"); renderCatalog(); }
        if (button.dataset.crumb === "records") { setFlowView("records"); renderRecords(); }
      });
    });
  }

  function renderManageMenu() {
    el("manageMenu").innerHTML = data.managementModules.filter(item => item.id !== "home").map(item => `
      <button class="nav-menu-item ${item.id === state.module ? "active" : ""}" data-module="${item.id}" type="button">
        ${item.title}
      </button>
    `).join("");
    el("manageMenu").querySelectorAll(".nav-menu-item").forEach(button => button.addEventListener("click", () => {
      if (button.dataset.module === "flow") state.view = "catalog";
      showModule(button.dataset.module);
      if (button.dataset.module === "flow") renderCatalog();
    }));
  }

  function renderHome() {
    el("moduleGrid").innerHTML = data.managementModules.filter(item => item.id !== "home").map(item => `
      <article class="module-card el-card" data-module-card="${item.id}" tabindex="0" role="button">
        <div class="module-card-top">
          <span class="module-mark">${item.title.slice(0, 2)}</span>
          <span class="badge el-tag ${item.id === "flow" ? "el-tag--success green" : "blue"}">${item.status}</span>
        </div>
        <h2>${item.title}</h2>
        <p>${item.desc}</p>
        <div class="module-card-bottom">
          <strong>${item.metric}</strong>
          <button type="button" class="el-button el-button--primary primary" data-module-open="${item.id}">${item.action}</button>
        </div>
      </article>
    `).join("");
    el("moduleGrid").querySelectorAll("[data-module-card], [data-module-open]").forEach(item => {
      item.addEventListener("click", event => {
        const target = item.dataset.moduleCard || item.dataset.moduleOpen;
        event.stopPropagation();
        if (target === "flow") state.view = "catalog";
        showModule(target);
        if (target === "flow") renderCatalog();
      });
    });
  }

  function syncClearButtons() {
    el("clearDepartmentSearch").classList.toggle("hidden", !el("departmentSearch").value);
    el("clearTemplateSearch").classList.toggle("hidden", !el("templateSearch").value);
  }

  function renderCatalog() {
    syncClearButtons();
    const deptQuery = el("departmentSearch").value.trim().toLowerCase();
    const departments = ["全部", ...Array.from(new Set(data.templates.map(item => item.department)))];
    const visibleDepartments = departments.filter(dept => !deptQuery || dept.toLowerCase().includes(deptQuery));
    el("departmentList").innerHTML = visibleDepartments.map(dept => {
      const count = dept === "全部" ? data.templates.length : data.templates.filter(item => item.department === dept).length;
      return `<button type="button" class="department-button el-button ${dept === state.selectedDepartment ? "active" : ""}" data-dept="${dept}"><span>${dept}</span><span class="badge el-tag">${count}</span></button>`;
    }).join("");
    el("departmentList").querySelectorAll("[data-dept]").forEach(button => {
      button.addEventListener("click", () => { state.selectedDepartment = button.dataset.dept; state.page = 1; renderCatalog(); });
    });

    const q = el("templateSearch").value.trim().toLowerCase();
    const status = el("statusFilter").value;
    const filtered = data.templates.filter(item => {
      const deptOk = state.selectedDepartment === "全部" || item.department === state.selectedDepartment;
      const statusOk = status === "all" || item.status === status;
      const text = `${item.name} ${item.department} ${item.owner} ${item.desc} ${item.tags.join(" ")}`.toLowerCase();
      return deptOk && statusOk && (!q || text.includes(q));
    });
    const totalPages = Math.max(1, Math.ceil(filtered.length / state.pageSize));
    if (state.page > totalPages) state.page = totalPages;
    const pageItems = filtered.slice((state.page - 1) * state.pageSize, state.page * state.pageSize);
    el("templateGrid").innerHTML = pageItems.map(item => `
      <article class="template-card el-card" data-card="${item.id}" tabindex="0" role="button">
        <div class="template-meta"><span class="badge el-tag blue">${item.department}</span><span class="badge el-tag ${item.status === "active" ? "el-tag--success green" : "el-tag--warning amber"}">${item.status === "active" ? "启用中" : "草稿"}</span></div>
        <h3>${item.name}</h3>
        <p>${item.desc}</p>
        <div class="template-meta"><span class="badge el-tag">${item.steps} 步</span><span class="badge el-tag">默认负责人：${item.owner}</span><span class="badge el-tag">${item.version}</span></div>
        <div class="template-actions"><button type="button" class="el-button" data-config="${item.id}">配置模板</button><button type="button" class="el-button el-button--primary primary" data-records="${item.id}">查看流程</button></div>
      </article>
    `).join("");
    el("templateGrid").querySelectorAll("[data-card]").forEach(card => card.addEventListener("click", () => openRecords(card.dataset.card)));
    el("templateGrid").querySelectorAll("[data-records], [data-config]").forEach(button => {
      button.addEventListener("click", event => {
        event.stopPropagation();
        if (button.dataset.config) toast("后续进入模板配置：步骤、字段、负责人、通知规则。");
        if (button.dataset.records) openRecords(button.dataset.records);
      });
    });
    renderPagination(filtered.length, totalPages);
    renderRecentRows();
  }

  function renderPagination(totalCount, totalPages) {
    const pager = el("templatePagination");
    if (totalCount <= state.pageSize) { pager.innerHTML = `<span class="pagination-total">共 ${totalCount} 条</span>`; return; }
    const pages = [];
    const add = page => pages.push(`<button type="button" class="el-button ${page === state.page ? "active" : ""}" data-page="${page}">${page}</button>`);
    add(1);
    const start = Math.max(2, state.page - 1);
    const end = Math.min(totalPages - 1, state.page + 1);
    if (start > 2) pages.push("<span>...</span>");
    for (let page = start; page <= end; page += 1) add(page);
    if (end < totalPages - 1) pages.push("<span>...</span>");
    if (totalPages > 1) add(totalPages);
    pager.innerHTML = `<span class="pagination-total">共 ${totalCount} 条</span><button class="el-button" type="button" data-prev ${state.page === 1 ? "disabled" : ""}>‹</button>${pages.join("")}<button class="el-button" type="button" data-next ${state.page === totalPages ? "disabled" : ""}>›</button><span class="pagination-jumper">前往 <input class="el-input__inner" id="pageJump" type="number" min="1" max="${totalPages}" value="${state.page}"> 页</span>`;
    pager.querySelectorAll("[data-page]").forEach(button => button.addEventListener("click", () => { state.page = Number(button.dataset.page); renderCatalog(); }));
    const prev = pager.querySelector("[data-prev]");
    const next = pager.querySelector("[data-next]");
    if (prev) prev.addEventListener("click", () => { state.page = Math.max(1, state.page - 1); renderCatalog(); });
    if (next) next.addEventListener("click", () => { state.page = Math.min(totalPages, state.page + 1); renderCatalog(); });
    el("pageJump").addEventListener("change", event => { state.page = Math.min(totalPages, Math.max(1, Number(event.target.value) || 1)); renderCatalog(); });
  }

  function renderRecentRows() {
    el("recentRows").innerHTML = data.instances.filter(item => state.selectedDepartment === "全部" || item.department === state.selectedDepartment).map(item => `
      <tr><td><strong>${item.name}</strong></td><td>${item.department}</td><td>${item.current}</td><td>${item.owner}</td><td>${item.progress}</td><td><button class="el-button" type="button" data-recent="${item.templateId}">查看</button></td></tr>
    `).join("");
    el("recentRows").querySelectorAll("[data-recent]").forEach(button => button.addEventListener("click", () => openRecords(button.dataset.recent)));
  }

  function openRecords(templateId) {
    state.selectedTemplateId = templateId;
    state.recordTab = "active";
    setFlowView("records");
    renderRecords();
  }

  function renderRecords() {
    const tpl = template();
    el("recordsTitle").textContent = tpl.name;
    el("recordsDesc").textContent = tpl.desc;
    el("recordsDepartment").textContent = tpl.department;
    el("recordsOwner").textContent = tpl.owner;
    el("recordsVersion").textContent = tpl.version;
    el("recordsSteps").textContent = `${tpl.steps} 步`;
    document.querySelectorAll(".record-tab").forEach(tab => tab.classList.toggle("active", tab.dataset.recordTab === state.recordTab));
    const rows = data.instances.filter(item => item.templateId === state.selectedTemplateId && item.status === state.recordTab);
    el("recordRows").innerHTML = rows.length ? rows.map(item => `<tr><td><strong>${item.name}</strong></td><td><span class="badge el-tag ${item.status === "active" ? "blue" : "el-tag--success green"}">${item.status === "active" ? "进行中" : "已完成"}</span></td><td>${item.current}</td><td>${item.owner}</td><td>${item.progress}</td><td>${item.updated}</td><td><button type="button" class="el-button el-button--primary primary" data-instance="${item.id}">进入</button></td></tr>`).join("") : `<tr><td colspan="7">暂无流程。</td></tr>`;
    el("recordRows").querySelectorAll("[data-instance]").forEach(button => button.addEventListener("click", () => { state.selectedInstanceId = button.dataset.instance; openDetail(); }));
  }

  function openDetail() {
    state.steps = data.steps.map(item => ({ ...item }));
    state.activeStep = 0;
    setFlowView("detail");
    renderDetail();
  }

  function renderDetail() {
    const inst = instance();
    const step = state.steps[state.activeStep];
    el("instanceNameDisplay").textContent = inst.name;
    el("detailInstanceName").textContent = inst.name;
    el("sideInstanceName").textContent = inst.name;
    el("currentStepName").textContent = step.name;
    el("completeMetric").textContent = `${state.steps.filter(item => item.status === "done").length}/${state.steps.length}`;
    el("activeStepTitle").textContent = `${state.activeStep + 1}. ${step.name}`;
    el("activeStepDesc").textContent = step.desc;
    renderStepBar();
    renderStepList();
    renderAssignTargets();
    renderSubTasks([step.owner]);
    renderLogs();
    renderBreadcrumb();
  }

  function renderStepBar() {
    el("stepBar").innerHTML = state.steps.map((step, index) => `<button type="button" class="step-node ${step.status === "done" ? "done" : ""} ${index === state.activeStep ? "current" : ""}" data-step="${index}"><span>${index + 1}</span><strong>${step.name}</strong></button>`).join("");
    el("stepBar").querySelectorAll("[data-step]").forEach(button => button.addEventListener("click", () => { state.activeStep = Number(button.dataset.step); renderDetail(); }));
  }

  function renderStepList() {
    el("stepList").innerHTML = state.steps.map((step, index) => `<button type="button" class="step-item ${index === state.activeStep ? "active" : ""}" data-step="${index}"><span class="step-index">${index + 1}</span><span class="step-text"><strong>${step.name}</strong><span>${step.owner}</span></span></button>`).join("");
    el("stepList").querySelectorAll("[data-step]").forEach(button => button.addEventListener("click", () => { state.activeStep = Number(button.dataset.step); renderDetail(); }));
  }

  function renderAssignTargets() {
    const options = el("assignType").value === "group" ? Object.keys(data.groups) : data.people;
    el("assignTarget").innerHTML = options.map(name => `<option value="${name}">${name}</option>`).join("");
  }

  function renderSubTasks(owners) {
    el("subTaskList").innerHTML = owners.map(owner => `<div class="sub-task"><div><strong>${state.steps[state.activeStep].name}确认</strong><br><span>重新分配后生成的会签任务</span></div><span>${owner}</span><span class="badge el-tag el-tag--warning amber">待处理</span></div>`).join("");
  }

  function renderLogs() {
    el("logList").innerHTML = [["微信机器人", `已发送待办提醒给 ${state.steps[state.activeStep].owner}：请完成${state.steps[state.activeStep].name}。`], ["流程创建", `${instance().name} 流程已创建，系统通知第 1 步负责人。`]].map(item => `<div class="log-item"><strong>${item[0]}</strong><span>${item[1]}</span></div>`).join("");
  }

  function completeStep() {
    state.steps[state.activeStep].status = "done";
    if (state.activeStep < state.steps.length - 1) {
      state.activeStep += 1;
      state.steps[state.activeStep].status = "current";
    }
    renderDetail();
    toast("已自动签名，并通知下一步负责人。");
  }

  function bindEvents() {
    el("homeNav").addEventListener("click", () => { showModule("home"); renderHome(); });
    el("flowReferenceFrame").addEventListener("load", syncReferenceFrame);
    ["departmentSearch", "templateSearch"].forEach(id => el(id).addEventListener("input", () => { state.page = 1; renderCatalog(); }));
    el("clearDepartmentSearch").addEventListener("click", () => { el("departmentSearch").value = ""; state.page = 1; renderCatalog(); el("departmentSearch").focus(); });
    el("clearTemplateSearch").addEventListener("click", () => { el("templateSearch").value = ""; state.page = 1; renderCatalog(); el("templateSearch").focus(); });
    el("statusFilter").addEventListener("change", () => { state.page = 1; renderCatalog(); });
    document.querySelectorAll(".record-tab").forEach(tab => tab.addEventListener("click", () => { state.recordTab = tab.dataset.recordTab; renderRecords(); }));
    el("createTemplateBtn").addEventListener("click", () => toast("后续会进入新增流程模板页面。"));
    el("editInstanceBtn").addEventListener("click", () => { el("instanceNameInput").value = instance().name; el("cloudPathInput").value = state.cloudPath; el("instanceEditor").classList.remove("hidden"); });
    el("cancelInstanceBtn").addEventListener("click", () => el("instanceEditor").classList.add("hidden"));
    el("confirmInstanceBtn").addEventListener("click", () => { instance().name = el("instanceNameInput").value.trim() || instance().name; state.cloudPath = el("cloudPathInput").value.trim() || state.cloudPath; el("instanceEditor").classList.add("hidden"); renderDetail(); toast("流程实例信息已更新。"); });
    el("assignType").addEventListener("change", renderAssignTargets);
    el("applyAssignBtn").addEventListener("click", () => { const target = el("assignTarget").value; const owners = el("assignType").value === "group" ? data.groups[target] : [target]; state.steps[state.activeStep].owner = target; renderStepList(); renderSubTasks(owners); renderLogs(); toast("责任分配已应用。"); });
    el("completeStepBtn").addEventListener("click", completeStep);
    el("copyCloudPathBtn").addEventListener("click", async () => { try { await navigator.clipboard.writeText(state.cloudPath); toast("共享盘路径已复制。"); } catch (error) { toast("浏览器未允许复制，请手动复制共享盘路径。"); } });
  }

  function syncReferenceFrame() {
    const frame = el("flowReferenceFrame");
    const doc = frame.contentDocument;
    if (!doc || doc.getElementById("embeddedFlowOverrides")) return;
    const style = doc.createElement("style");
    style.id = "embeddedFlowOverrides";
    style.textContent = `
      .menu-bar { display: none !important; }
      .app { padding-top: 0 !important; min-height: 100vh !important; }
      .page-shell {
        width: 100% !important;
        min-height: calc(112vh - 8vh - 8px) !important;
        height: auto !important;
        margin-bottom: 0 !important;
        display: flex !important;
        flex-direction: column !important;
      }
      .workspace {
        flex: 1 1 auto !important;
        height: auto !important;
        min-height: 0 !important;
        align-items: stretch !important;
      }
      .workspace > .panel,
      .workspace > .side-stack {
        height: 100% !important;
      }
      body { background: #f5f7fb !important; }
    `;
    doc.head.appendChild(style);
  }

  renderManageMenu();
  bindEvents();
  renderHome();
  showModule("home");
  window.setTimeout(syncReferenceFrame, 800);
  renderCatalog();
})();
