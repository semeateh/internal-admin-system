<template>
  <div class="app">
    <LoginView v-if="!isAuthenticated" @login="handleLogin" />
    <template v-else>
    <header class="top-nav">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="nav-item" :class="{ active: currentModule === 'home' }" type="button" @click="openModule('home')">首页</button>
          <div class="nav-dropdown">
            <button class="nav-item" :class="{ active: currentModule !== 'home' }" type="button">管理</button>
            <div class="nav-menu">
              <button
                v-for="module in visibleManagementModules.filter(item => item.id !== 'home')"
                :key="module.id"
                class="nav-menu-item"
                :class="{ active: currentModule === module.id }"
                type="button"
                @click="openModule(module.id)"
              >
                {{ module.title }}
              </button>
            </div>
          </div>
          <div class="nav-dropdown">
            <button class="nav-item" type="button">设置</button>
            <div class="nav-menu">
              <button class="nav-menu-item" type="button">重置密码</button>
              <button class="nav-menu-item" type="button">错误追踪解析</button>
            </div>
          </div>
        </div>
        <div class="nav-right">
          <div class="nav-dropdown">
            <button class="nav-item" type="button">{{ currentUser.name || "账户" }}</button>
            <div class="nav-menu nav-menu-right">
              <button class="nav-menu-item" type="button" @click="handleLogout">退出登录</button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="shell">
      <div v-if="currentModule !== 'home'" class="page-head">
        <nav class="breadcrumb">
          <template v-for="(crumb, index) in breadcrumbs">
            <span v-if="index" :key="`${crumb.label}-sep`">></span>
            <button v-if="crumb.action" :key="crumb.label" type="button" @click="crumb.action">{{ crumb.label }}</button>
            <strong v-else :key="crumb.label">{{ crumb.label }}</strong>
          </template>
        </nav>
        <div v-if="currentModule === 'flow'" class="page-actions">
          <el-button v-if="flowView === 'catalog' && hasPermission('flow.template.manage')" type="primary" icon="el-icon-plus" @click="createFlowTemplate">新增流程模板</el-button>
          <el-button v-if="flowView === 'records'" icon="el-icon-back" @click="showCatalog">返回流程列表</el-button>
          <el-button v-if="flowView === 'records' && hasPermission('flow.template.manage')" icon="el-icon-setting" @click="showDesigner(selectedTemplateId)">配置模板</el-button>
          <el-button v-if="flowView === 'records' && hasPermission('flow.instance.start')" type="primary" icon="el-icon-plus" @click="createFlowInstance">新建流程</el-button>
          <el-button v-if="flowView === 'designer'" icon="el-icon-back" @click="showCatalog">返回流程列表</el-button>
          <el-button v-if="flowView === 'designer' && hasPermission('flow.template.manage')" icon="el-icon-check" @click="saveTemplateDesigner">保存模板</el-button>
          <el-button v-if="flowView === 'designer' && hasPermission('flow.instance.start')" type="primary" icon="el-icon-video-play" @click="createFlowInstance">使用此模板发起流程</el-button>
          <el-button v-if="flowView === 'detail'" icon="el-icon-back" @click="showCatalog">返回流程列表</el-button>
          <el-button v-if="flowView === 'detail'" type="primary" icon="el-icon-document-checked" @click="$message.success('已生成产品 Release 查检表。')">生成查检表</el-button>
        </div>
      </div>

      <HomeDashboard v-if="currentModule === 'home'" :modules="visibleManagementModules" @open-module="openModule" />

      <template v-else-if="currentModule === 'flow'">
        <FlowCatalog
          v-if="flowView === 'catalog'"
          :templates="templates"
          :instances="instances"
          :can-manage-template="hasPermission('flow.template.manage')"
          @open-records="showRecords"
          @configure-template="showDesigner"
        />
        <FlowRecords
          v-else-if="flowView === 'records'"
          :template="selectedTemplate"
          :instances="instances"
          @open-detail="showDetail"
        />
        <TemplateDesigner
          v-else-if="flowView === 'designer'"
          ref="templateDesigner"
          :template="selectedTemplate"
          :steps="steps"
          :people="people"
          :groups="groups"
        />
        <FlowDetail
          v-else-if="flowView === 'detail' && selectedInstance"
          :key="detailKey"
          :instance="selectedInstance"
          :steps="steps"
          :people="people"
          :groups="groups"
          :start-editing="startEditingDetail"
          @update-instance="updateInstance"
          @instance-updated="syncInstanceDetail"
        />
      </template>

      <PlaceholderModule v-else :module-title="currentModuleInfo.title" />
    </main>
    </template>
  </div>
</template>

<script>
import LoginView from "./components/LoginView.vue";
import HomeDashboard from "./components/HomeDashboard.vue";
import FlowCatalog from "./components/FlowCatalog.vue";
import FlowRecords from "./components/FlowRecords.vue";
import TemplateDesigner from "./components/TemplateDesigner.vue";
import FlowDetail from "./components/FlowDetail.vue";
import PlaceholderModule from "./components/PlaceholderModule.vue";
import { fetchCurrentUser } from "./api/auth.js";
import { createInstance, fetchInstance, fetchInstances, updateInstanceRecord } from "./api/instances.js";
import { clearAuthToken, getAuthToken } from "./api/request.js";
import { createTemplate, fetchTemplate, fetchTemplates, saveTemplate } from "./api/templates.js";
import { groups, instances as mockInstances, managementModules, people, steps as mockSteps, templates as mockTemplates } from "./data/flow-data.js";

export default {
  name: "App",
  components: { LoginView, HomeDashboard, FlowCatalog, FlowRecords, TemplateDesigner, FlowDetail, PlaceholderModule },
  data() {
    return {
      currentUser: {},
      isAuthenticated: Boolean(getAuthToken()),
      managementModules,
      people,
      groups,
      templates: JSON.parse(JSON.stringify(mockTemplates)),
      instances: JSON.parse(JSON.stringify(mockInstances)),
      steps: JSON.parse(JSON.stringify(mockSteps)),
      apiAvailable: false,
      currentModule: "home",
      flowView: "catalog",
      selectedTemplateId: "release-market-sales",
      selectedInstanceId: "inst-1",
      startEditingDetail: false,
      detailKey: 0
    };
  },
  computed: {
    currentModuleInfo() {
      return this.managementModules.find(item => item.id === this.currentModule) || { title: "模块建设中" };
    },
    visibleManagementModules() {
      return this.managementModules.filter(module => {
        if (module.id === "home") return true;
        const required = {
          flow: "flow.instance.view",
          template: "flow.template.manage",
          people: "employee.manage",
          permission: "role.manage"
        }[module.id];
        return !required || this.hasPermission(required);
      });
    },
    selectedTemplate() {
      return this.templates.find(item => item.id === this.selectedTemplateId) || this.templates[0];
    },
    selectedInstance() {
      return this.instances.find(item => item.id === this.selectedInstanceId) || this.instances[0];
    },
    breadcrumbs() {
      if (this.currentModule !== "flow") return [{ label: "首页", action: () => this.openModule("home") }, { label: this.currentModuleInfo.title }];
      const crumbs = [{ label: "首页", action: () => this.openModule("home") }, { label: "流程管理", action: this.flowView === "catalog" ? null : this.showCatalog }];
      if (["records", "designer", "detail"].includes(this.flowView)) crumbs.push({ label: this.selectedTemplate.name, action: this.flowView === "detail" ? () => this.showRecords(this.selectedTemplateId) : null });
      if (this.flowView === "designer") crumbs.push({ label: "配置模板" });
      if (this.flowView === "detail") crumbs.push({ label: this.selectedInstance.name });
      return crumbs;
    }
  },
  mounted() {
    window.addEventListener("auth-unauthorized", this.handleLogout);
    if (this.isAuthenticated) this.bootstrapAuthenticatedApp();
  },
  beforeDestroy() {
    window.removeEventListener("auth-unauthorized", this.handleLogout);
  },
  methods: {
    hasPermission(code) {
      return Boolean(this.currentUser.permissions?.includes(code));
    },
    async bootstrapAuthenticatedApp() {
      try {
        this.currentUser = await fetchCurrentUser();
        await this.loadFlowData();
      } catch (error) {
        this.handleLogout();
      }
    },
    async handleLogin(user) {
      this.currentUser = user || {};
      this.isAuthenticated = true;
      await this.loadFlowData();
    },
    handleLogout() {
      clearAuthToken();
      this.currentUser = {};
      this.isAuthenticated = false;
      this.currentModule = "home";
      this.flowView = "catalog";
    },
    async loadFlowData() {
      try {
        const [remoteTemplates, remoteInstances] = await Promise.all([fetchTemplates(), fetchInstances()]);
        if (remoteTemplates.length) {
          this.templates = remoteTemplates;
          if (!this.templates.some(item => item.id === this.selectedTemplateId)) this.selectedTemplateId = this.templates[0].id;
        }
        if (remoteInstances.length) {
          this.instances = remoteInstances;
          if (!this.instances.some(item => item.id === this.selectedInstanceId)) this.selectedInstanceId = this.instances[0].id;
        }
        this.apiAvailable = true;
      } catch (error) {
        this.apiAvailable = false;
        console.info("Flow API unavailable, using local mock data.", error.message);
      }
    },
    openModule(module) {
      if (!this.visibleManagementModules.some(item => item.id === module)) {
        this.$message.warning("当前账号没有该功能权限。");
        return;
      }
      this.currentModule = module;
      if (module === "flow") this.flowView = "catalog";
    },
    showCatalog() {
      this.currentModule = "flow";
      this.flowView = "catalog";
    },
    showRecords(templateId) {
      this.selectedTemplateId = templateId;
      this.flowView = "records";
    },
    async showDesigner(templateId) {
      if (!this.hasPermission("flow.template.manage")) {
        this.$message.warning("当前账号没有配置模板权限。");
        return;
      }
      this.selectedTemplateId = templateId;
      await this.loadTemplateSteps(templateId);
      this.flowView = "designer";
    },
    async showDetail(instanceId, startEditing = false) {
      this.selectedInstanceId = instanceId;
      this.startEditingDetail = startEditing;
      await this.loadInstanceDetail(instanceId);
      this.detailKey += 1;
      this.flowView = "detail";
    },
    async createFlowInstance() {
      if (!this.hasPermission("flow.instance.start")) {
        this.$message.warning("当前账号没有新建流程权限。");
        return;
      }
      const template = this.selectedTemplate;
      const now = new Date();
      const pad = value => String(value).padStart(2, "0");
      const createdAt = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
      const name = `${template.name} - 新建实例`;
      if (this.apiAvailable) {
        try {
          const remoteInstance = await createInstance({ templateId: template.id, name, cloudPath: "" });
          this.instances.unshift(remoteInstance);
          if (remoteInstance.steps?.length) this.steps = remoteInstance.steps;
          await this.showDetail(remoteInstance.id, true);
          this.$message.success("已新建流程，请确认实例名称和共享盘路径。");
          return;
        } catch (error) {
          this.apiAvailable = false;
          this.$message.warning(`后端新建失败，已切回本地演示：${error.message}`);
        }
      }
      const instance = {
        id: `new-${Date.now()}`,
        templateId: template.id,
        name,
        department: template.department,
        status: "active",
        current: this.steps[0].name,
        owner: template.owner,
        progress: `0/${template.steps}`,
        updated: createdAt,
        cloudPath: ""
      };
      this.instances.unshift(instance);
      await this.showDetail(instance.id, true);
      this.$message.success("已新建流程，请确认实例名称和共享盘路径。");
    },
    async createFlowTemplate() {
      if (!this.hasPermission("flow.template.manage")) {
        this.$message.warning("当前账号没有新增模板权限。");
        return;
      }
      if (!this.apiAvailable) {
        this.$message.error("后端服务不可用，模板无法创建。请联系开发人员/管理员。");
        return;
      }
      try {
        const base = this.selectedTemplate || {};
        const template = await createTemplate({
          name: `新建流程模板 ${new Date().toISOString().slice(0, 10)}`,
          department: base.department,
          owner: this.currentUser.name,
          description: ""
        });
        this.templates.unshift(template);
        this.selectedTemplateId = template.id;
        if (template.stepDetails?.length) this.steps = template.stepDetails;
        this.flowView = "designer";
        this.$message.success("模板已创建，请继续配置步骤。");
      } catch (error) {
        this.$message.error(error.message || "模板创建失败。请联系开发人员/管理员。");
      }
    },
    async saveTemplateDesigner() {
      if (!this.hasPermission("flow.template.manage")) {
        this.$message.warning("当前账号没有保存模板权限。");
        return;
      }
      if (!this.apiAvailable) {
        this.$message.error("后端服务不可用，模板无法保存。请联系开发人员/管理员。");
        return;
      }
      const payload = this.$refs.templateDesigner?.buildPayload?.();
      if (!payload) {
        this.$message.error("未读取到模板编辑内容。请联系开发人员/管理员。");
        return;
      }
      try {
        const template = await saveTemplate(this.selectedTemplateId, payload);
        const index = this.templates.findIndex(item => item.id === template.id);
        if (index >= 0) this.$set(this.templates, index, template);
        if (template.stepDetails?.length) this.steps = template.stepDetails;
        await this.loadFlowData();
        this.$message.success("模板已保存。");
      } catch (error) {
        this.$message.error(error.message || "模板保存失败。请联系开发人员/管理员。");
      }
    },
    async updateInstance(payload) {
      if (this.apiAvailable && !String(payload.id).startsWith("new-")) {
        try {
          const remoteInstance = await updateInstanceRecord(payload.id, payload);
          const target = this.instances.find(item => item.id === payload.id);
          if (target) Object.assign(target, remoteInstance);
          this.$message.success("流程实例信息已更新。");
          return;
        } catch (error) {
          this.apiAvailable = false;
          this.$message.warning(`后端更新失败，已切回本地演示：${error.message}`);
        }
      }
      const target = this.instances.find(item => item.id === payload.id);
      if (target) Object.assign(target, payload);
      this.$message.success("流程实例信息已更新。");
    },
    async loadTemplateSteps(templateId) {
      if (!this.apiAvailable) return;
      try {
        const template = await fetchTemplate(templateId);
        if (template.stepDetails?.length) this.steps = template.stepDetails;
      } catch (error) {
        this.apiAvailable = false;
        console.info("Template detail API unavailable, using local steps.", error.message);
      }
    },
    async loadInstanceDetail(instanceId) {
      if (!this.apiAvailable || String(instanceId).startsWith("new-")) return;
      try {
        const instance = await fetchInstance(instanceId);
        this.syncInstanceDetail(instance);
      } catch (error) {
        this.apiAvailable = false;
        console.info("Instance detail API unavailable, using local steps.", error.message);
      }
    },
    syncInstanceDetail(instance) {
      const target = this.instances.find(item => item.id === instance.id);
      if (target) Object.assign(target, instance);
      if (instance.steps?.length) this.steps = instance.steps;
    }
  }
};
</script>
