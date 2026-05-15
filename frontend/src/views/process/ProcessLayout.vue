<template>
  <section>
    <div class="page-head">
      <nav class="breadcrumb">
        <template v-for="(crumb, index) in breadcrumbs">
          <span v-if="index" :key="`${crumb.label}-sep`">></span>
          <button v-if="crumb.action" :key="crumb.label" type="button" @click="crumb.action">{{ crumb.label }}</button>
          <strong v-else :key="crumb.label">{{ crumb.label }}</strong>
        </template>
      </nav>
      <div class="page-actions">
        <el-button v-if="isCatalog && canManageTemplate" type="primary" icon="el-icon-plus" @click="createFlowTemplate">新增流程模板</el-button>
        <el-button v-if="isRecords" icon="el-icon-back" @click="showCatalog">返回流程列表</el-button>
        <el-button v-if="isRecords && canManageTemplate" icon="el-icon-setting" @click="showDesigner(selectedTemplateId)">配置模板</el-button>
        <el-button v-if="isRecords && canStartInstance" type="primary" icon="el-icon-plus" @click="createFlowInstance">新建流程</el-button>
        <el-button v-if="isDesigner" icon="el-icon-back" @click="showCatalog">返回流程列表</el-button>
        <el-button v-if="isDesigner && canManageTemplate" icon="el-icon-check" @click="saveTemplateDesigner">保存模板</el-button>
        <el-button v-if="isDesigner && canStartInstance" type="primary" icon="el-icon-video-play" @click="createFlowInstance">使用此模板发起流程</el-button>
        <el-button v-if="isDetail" icon="el-icon-back" @click="showCatalog">返回流程列表</el-button>
        <el-button v-if="isDetail" type="primary" icon="el-icon-document-checked" @click="generateInstanceChecklist">生成查检表</el-button>
      </div>
    </div>

    <router-view
      ref="routeView"
      :key="detailKey"
      :templates="templates"
      :instances="instances"
      :template="selectedTemplate"
      :instance="selectedInstance"
      :steps="steps"
      :people="people"
      :groups="groups"
      :current-user="currentUser"
      :can-manage-template="canManageTemplate"
      :can-delete-instance="canManageTemplate"
      :start-editing="startEditingDetail"
      @open-records="showRecords"
      @configure-template="showDesigner"
      @open-detail="showDetail"
      @delete-instance="deleteFlowInstance"
      @update-instance="updateInstance"
      @instance-updated="syncInstanceDetail"
    />
  </section>
</template>

<script>
import { fetchPeopleDirectory } from "@/api/directory.js";
import { createInstance, deleteInstance, fetchInstance, fetchInstances, generateChecklist, updateInstanceRecord } from "@/api/instances.js";
import { createTemplate, fetchTemplate, fetchTemplates, saveTemplate } from "@/api/templates.js";
import { hasPermission } from "@/utils/permission.js";

export default {
  name: "ProcessLayout",
  props: {
    currentUser: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      people: [],
      groups: {},
      templates: [],
      instances: [],
      steps: [],
      apiAvailable: false,
      startEditingDetail: false,
      detailKey: 0
    };
  },
  computed: {
    routeName() { return this.$route.name; },
    selectedTemplateId() {
      return this.$route.params.templateId || this.selectedInstance?.templateId || this.templates[0]?.id || "";
    },
    selectedInstanceId() {
      return this.$route.params.instanceId || this.instances[0]?.id || "";
    },
    selectedTemplate() {
      return this.templates.find(item => item.id === this.selectedTemplateId) || this.templates[0];
    },
    selectedInstance() {
      return this.instances.find(item => item.id === this.selectedInstanceId) || this.instances[0];
    },
    canManageTemplate() { return hasPermission(this.currentUser, "flow.template.manage"); },
    canStartInstance() { return hasPermission(this.currentUser, "flow.instance.start"); },
    isCatalog() { return this.routeName === "process-catalog"; },
    isRecords() { return this.routeName === "process-records"; },
    isDesigner() { return this.routeName === "process-designer"; },
    isDetail() { return this.routeName === "process-detail"; },
    breadcrumbs() {
      const crumbs = [
        { label: "首页", action: () => this.$router.push({ name: "home" }) },
        { label: "流程管理", action: this.isCatalog ? null : this.showCatalog }
      ];
      if (this.selectedTemplate && !this.isCatalog) {
        crumbs.push({
          label: this.selectedTemplate.name,
          action: this.isDetail ? () => this.showRecords(this.selectedTemplate.id) : null
        });
      }
      if (this.isDesigner) crumbs.push({ label: "配置模板" });
      if (this.isDetail && this.selectedInstance) crumbs.push({ label: this.selectedInstance.name });
      return crumbs;
    }
  },
  watch: {
    "$route.name": {
      immediate: true,
      async handler(name) {
        if (name === "process-designer" && this.selectedTemplateId) await this.loadTemplateSteps(this.selectedTemplateId);
        if (name === "process-detail" && this.selectedInstanceId) await this.loadInstanceDetail(this.selectedInstanceId);
      }
    }
  },
  async mounted() {
    await this.loadFlowData();
  },
  methods: {
    async loadFlowData() {
      try {
        const [remoteTemplates, remoteInstances, directory] = await Promise.all([fetchTemplates(), fetchInstances(), fetchPeopleDirectory()]);
        this.people = directory.people || [];
        this.groups = directory.groups || {};
        this.templates = remoteTemplates || [];
        this.instances = remoteInstances || [];
        this.apiAvailable = true;
      } catch (error) {
        this.apiAvailable = false;
        this.$message.error(`后端服务不可用：${error.message}`);
      }
    },
    showCatalog() {
      this.$router.push({ name: "process-catalog" });
    },
    showRecords(templateId) {
      this.$router.push({ name: "process-records", params: { templateId } });
    },
    async showDesigner(templateId) {
      if (!this.canManageTemplate) {
        this.$message.warning("当前账号没有配置模板权限。");
        return;
      }
      await this.loadTemplateSteps(templateId);
      this.$router.push({ name: "process-designer", params: { templateId } });
    },
    async showDetail(instanceId, startEditing = false) {
      this.startEditingDetail = startEditing;
      await this.loadInstanceDetail(instanceId);
      this.detailKey += 1;
      this.$router.push({ name: "process-detail", params: { instanceId } });
    },
    async createFlowInstance() {
      if (!this.canStartInstance) {
        this.$message.warning("当前账号没有新建流程权限。");
        return;
      }
      const template = this.selectedTemplate;
      const name = `${template.name} - 新建实例`;
      try {
        const remoteInstance = await createInstance({ templateId: template.id, name, cloudPath: "" });
        this.instances.unshift(remoteInstance);
        if (remoteInstance.steps?.length) this.steps = remoteInstance.steps;
        await this.showDetail(remoteInstance.id, true);
        this.$message.success("已新建流程，请确认实例名称和共享盘路径。");
      } catch (error) {
        this.$message.error(error.message || "流程新建失败。请联系开发人员/管理员。");
      }
    },
    async createFlowTemplate() {
      if (!this.canManageTemplate) {
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
        if (template.stepDetails?.length) this.steps = template.stepDetails;
        await this.showDesigner(template.id);
        this.$message.success("模板已创建，请继续配置步骤。");
      } catch (error) {
        this.$message.error(error.message || "模板创建失败。请联系开发人员/管理员。");
      }
    },
    async saveTemplateDesigner() {
      if (!this.canManageTemplate) {
        this.$message.warning("当前账号没有保存模板权限。");
        return;
      }
      if (!this.apiAvailable) {
        this.$message.error("后端服务不可用，模板无法保存。请联系开发人员/管理员。");
        return;
      }
      const payload = this.$refs.routeView?.buildPayload?.();
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
      try {
        const remoteInstance = await updateInstanceRecord(payload.id, payload);
        this.syncInstanceDetail(remoteInstance);
        this.$message.success("流程实例信息已更新。");
      } catch (error) {
        this.$message.error(error.message || "流程实例更新失败。请联系开发人员/管理员。");
      }
    },
    async deleteFlowInstance(row) {
      if (!this.canManageTemplate) {
        this.$message.warning("当前账号没有删除流程实例权限。");
        return;
      }
      try {
        await this.$confirm(`确定删除流程实例“${row.name}”吗？删除后将从列表中移除。`, "删除流程实例", {
          confirmButtonText: "删除",
          cancelButtonText: "取消",
          type: "warning"
        });
      } catch (_) {
        return;
      }
      try {
        await deleteInstance(row.id);
        this.instances = this.instances.filter(item => item.id !== row.id);
        this.$message.success("流程实例已删除。");
      } catch (error) {
        this.$message.error(error.message || "流程实例删除失败。请联系开发人员/管理员。");
      }
    },
    async loadTemplateSteps(templateId) {
      if (!this.apiAvailable && this.templates.length) return;
      try {
        const template = await fetchTemplate(templateId);
        if (template.stepDetails?.length) this.steps = template.stepDetails;
      } catch (error) {
        this.apiAvailable = false;
        this.$message.error(`模板详情加载失败：${error.message}`);
      }
    },
    async loadInstanceDetail(instanceId) {
      if (!instanceId || String(instanceId).startsWith("new-")) return;
      try {
        const instance = await fetchInstance(instanceId);
        this.syncInstanceDetail(instance);
      } catch (error) {
        this.apiAvailable = false;
        this.$message.error(`流程详情加载失败：${error.message}`);
      }
    },
    async generateInstanceChecklist() {
      try {
        const instance = await generateChecklist(this.selectedInstanceId);
        this.syncInstanceDetail(instance);
        this.$message.success(`查检表已生成：${instance.attachment?.fileName || "已归档"}`);
      } catch (error) {
        this.$message.error(error.message || "查检表生成失败。请联系开发人员/管理员。");
      }
    },
    syncInstanceDetail(instance) {
      const target = this.instances.find(item => item.id === instance.id);
      if (target) Object.assign(target, instance);
      else this.instances.unshift(instance);
      if (instance.steps?.length) this.steps = instance.steps;
    }
  }
};
</script>
