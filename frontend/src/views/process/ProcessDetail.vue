<template>
  <section>
    <el-card class="top-progress">
      <div class="instance-title-bar">
        <label>流程实例名称</label>
        <el-input v-if="editingMeta" v-model="draftName" />
        <strong v-else>{{ instance.name }}</strong>
        <div class="instance-title-actions">
          <el-button v-if="!editingMeta" icon="el-icon-edit" @click="editMeta">编辑</el-button>
          <el-button v-if="editingMeta" @click="editingMeta = false">取消</el-button>
          <el-button v-if="editingMeta" type="primary" icon="el-icon-check" @click="saveMeta">确认</el-button>
        </div>
        <label>共享盘路径</label>
        <el-input v-if="editingMeta" v-model="draftCloudPath" placeholder="填写内网共享盘路径" />
        <span v-else>{{ cloudPath || "未填写共享盘路径" }}</span>
        <span></span>
      </div>
      <div class="progress-head">
        <span>当前节点：<strong>{{ currentStep.name }}</strong></span>
        <el-progress :percentage="progressPercent" />
        <span>完成：<strong>{{ doneCount }}/{{ localSteps.length }}</strong></span>
      </div>
      <div class="progress-steps">
        <button
          v-for="(step, index) in localSteps"
          :key="step.id"
          type="button"
          class="progress-step"
          :class="{ current: index === activeIndex, done: isDone(step) }"
          @click="activeIndex = index"
        >
          <span class="step-node">{{ isDone(step) ? "✓" : index + 1 }}</span>
          <span>{{ step.name }}</span>
        </button>
      </div>
    </el-card>

    <main class="workspace">
      <el-card class="panel-card">
        <div slot="header">
          <h2 class="panel-title">流程进度</h2>
          <p class="panel-subtitle">示例：{{ instance.name }}</p>
        </div>
        <div class="step-list">
          <div v-for="(step, index) in localSteps" :key="step.id" class="step-item" :class="{ active: index === activeIndex }" @click="activeIndex = index">
            <div>
              <strong>{{ index + 1 }}. {{ step.name }}</strong><br>
              <span>{{ step.owner }}</span>
            </div>
            <el-tag :type="isDone(step) ? 'success' : step.status === 'current' ? '' : 'info'">{{ stepBadge(step) }}</el-tag>
          </div>
        </div>
      </el-card>

      <el-card class="panel-card">
        <div slot="header" class="card-header">
          <div>
            <h2 class="panel-title">{{ activeIndex + 1 }}. {{ currentStep.name }}</h2>
            <p class="panel-subtitle">{{ currentStep.desc }}</p>
          </div>
          <div class="page-actions">
            <el-button icon="el-icon-message" @click="remind">催办</el-button>
            <el-button v-if="isDone(currentStep) && !editingDone" icon="el-icon-edit" :disabled="!canEditCurrentStep" @click="editingDone = true">修改已完成内容</el-button>
            <el-button v-if="isDone(currentStep) && editingDone" type="primary" icon="el-icon-check" :disabled="!canEditCurrentStep || hasMissingRequired" @click="saveRevision">保存修订</el-button>
            <el-button v-if="!isDone(currentStep)" type="success" icon="el-icon-document-checked" :disabled="!canEditCurrentStep || currentStep.status !== 'current' || hasMissingRequired" @click="completeCurrentStep">完成当前任务</el-button>
          </div>
        </div>

        <el-alert v-if="isDone(currentStep) && !editingDone" title="已完成步骤默认只读，点击“修改已完成内容”后可追加修订签名。" type="info" show-icon :closable="false" />
        <el-alert v-if="!canEditCurrentStep" title="当前任务没有分配给你，不能填写或处理这个步骤。" type="warning" show-icon :closable="false" />
        <el-alert v-if="currentStep.status === 'current' && hasMissingRequired" :title="`请先填写必填项：${missingRequiredLabels.join('、')}`" type="warning" show-icon :closable="false" />

        <div class="form-section">
          <h3>本步骤填写</h3>
          <el-form label-position="top" size="medium" class="form-grid">
            <el-form-item v-for="field in currentStep.fields" :key="field.key || field.id" :label="`${field.label}${field.required ? ' *' : ''}`" :class="{ wide: field.type === 'textarea' || field.type === 'choice' || field.type === 'select' }">
              <el-radio-group v-if="field.type === 'choice' || field.type === 'select'" v-model="field.value" :disabled="fieldLocked" @change="persistCurrentFields">
                <el-radio-button v-for="option in field.options || []" :key="option" :label="option" />
              </el-radio-group>
              <el-input v-else-if="field.type === 'textarea'" v-model="field.value" type="textarea" :disabled="fieldLocked" @change="persistCurrentFields" />
              <el-date-picker v-else-if="field.type === 'date'" v-model="field.value" value-format="yyyy-MM-dd" :disabled="fieldLocked" @change="persistCurrentFields" />
              <el-input v-else v-model="field.value" :disabled="fieldLocked" :placeholder="`请输入${field.label}`" @change="persistCurrentFields" />
            </el-form-item>
          </el-form>
        </div>

        <div class="form-section">
          <h3>责任分配</h3>
          <div class="assignment-grid">
            <el-select v-model="assignMode" :disabled="fieldLocked" @change="refreshAssignee">
              <el-option label="指定人员" value="user" />
              <el-option label="指定小组" value="group" />
            </el-select>
            <el-select v-model="assignee" filterable :disabled="fieldLocked">
              <el-option v-for="name in assigneeOptions" :key="name" :label="name" :value="name" />
            </el-select>
            <el-select v-model="currentStep.rule" :disabled="fieldLocked">
              <el-option label="任一人完成" value="any" />
              <el-option label="全部完成" value="all" />
            </el-select>
            <el-button type="primary" icon="el-icon-check" :disabled="fieldLocked" @click="applyAssignment">应用分配</el-button>
          </div>
        </div>

        <div v-if="currentStep.tasks.length" class="form-section">
          <h3>子任务</h3>
          <div class="task-list">
            <div v-for="(task, index) in currentStep.tasks" :key="`${task.title}-${task.owner}`" class="task-row">
              <div><strong>{{ task.title }}</strong><br><span>{{ task.note }}</span></div>
              <span>{{ task.owner }}</span>
              <el-tag :type="task.status === 'done' ? 'success' : 'warning'">{{ task.status === "done" ? "已签名" : "待处理" }}</el-tag>
              <el-button size="mini" :disabled="!taskCanComplete(task) || task.status === 'done' || currentStep.status !== 'current' || hasMissingRequired" @click="completeTask(index)">完成</el-button>
            </div>
          </div>
        </div>
      </el-card>

      <aside class="side-stack">
        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">流程信息</h2><p class="panel-subtitle">最后归档到 Word 查检表</p></div>
          <div class="summary-grid">
            <div class="summary-item"><span>实例名称</span><strong>{{ instance.name }}</strong></div>
            <div class="summary-item"><span>共享盘</span><strong>{{ cloudPath || "未填写" }}</strong></div>
            <div class="summary-item"><span>PN</span><strong>{{ fieldValue("pn") || "待填写" }}</strong></div>
            <div class="summary-item"><span>归档状态</span><strong>{{ doneCount === localSteps.length ? "可生成" : "进行中" }}</strong></div>
          </div>
        </el-card>
        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">文档预览</h2><p class="panel-subtitle">完成后自动汇总为现有查检表</p></div>
          <div class="doc-row doc-head"><div>子流程</div><div>任务/填写内容</div><div>负责人</div><div>签名</div></div>
          <div v-for="row in docRows" :key="row[0]" class="doc-row"><div>{{ row[0] }}</div><div>{{ row[1] }}</div><div>{{ row[2] }}</div><div>{{ row[3] }}</div></div>
        </el-card>
        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">通知与操作日志</h2><p class="panel-subtitle">记录真实流程操作</p></div>
          <div class="log-list">
            <div v-for="event in events.slice().reverse()" :key="`${event.title}-${event.text}`" class="event">
              <strong>{{ event.title }}</strong>
              <p>{{ event.text }}</p>
            </div>
          </div>
        </el-card>
      </aside>
    </main>
  </section>
</template>

<script>
import { completeInstanceStep, completeInstanceTask, recordStepRevision, remindInstance, updateInstanceStepAssignment, updateInstanceStepFields } from "@/api/instances.js";

export default {
  name: "FlowDetail",
  props: {
    instance: { type: Object, required: true },
    steps: { type: Array, required: true },
    people: { type: Array, required: true },
    groups: { type: Object, required: true },
    currentUser: { type: Object, default: () => ({}) },
    startEditing: { type: Boolean, default: false }
  },
  data() {
    return {
      localSteps: JSON.parse(JSON.stringify(this.steps)),
      activeIndex: 0,
      editingMeta: this.startEditing,
      editingDone: false,
      draftName: this.instance.name,
      cloudPath: this.instance.cloudPath || "",
      draftCloudPath: this.instance.cloudPath || "",
      assignMode: "user",
      assignee: "",
      events: [
        { title: "流程创建", text: `${this.instance.owner} 创建了“${this.instance.name}”流程，系统通知第 1 步负责人。` },
        { title: "微信机器人", text: `已发送待办提醒给 ${this.instance.owner}：请完成预确认信息。` }
      ]
    };
  },
  computed: {
    currentStep() { return this.localSteps[this.activeIndex]; },
    doneCount() { return this.localSteps.filter(this.isDone).length; },
    progressPercent() { return Math.round(this.doneCount / this.localSteps.length * 100); },
    locked() { return this.isDone(this.currentStep) && !this.editingDone; },
    canManageCurrentStep() {
      return Boolean(this.currentUser?.permissions?.includes("flow.template.manage"));
    },
    canEditCurrentStep() {
      if (!this.currentStep) return false;
      const stepIsReachable = this.currentStep.status === "current" || this.isDone(this.currentStep);
      if (!stepIsReachable) return false;
      if (this.canManageCurrentStep) return true;
      const userName = this.currentUser?.name;
      if (!userName) return false;
      const assignedByTask = (this.currentStep.tasks || []).some(task => task.owner === userName);
      const assignedByStep = (this.currentStep.assignees || []).includes(userName);
      return assignedByTask || assignedByStep;
    },
    fieldLocked() { return this.locked || !this.canEditCurrentStep; },
    missingRequiredLabels() {
      return (this.currentStep?.fields || [])
        .filter(field => field.required && !String(field.value || "").trim())
        .map(field => field.label);
    },
    hasMissingRequired() { return this.missingRequiredLabels.length > 0; },
    assigneeOptions() { return this.assignMode === "group" ? Object.keys(this.groups) : this.people; },
    docRows() {
      return [
        ["PN 分配", `PN：${this.fieldValue("pn") || "待填写"}`, "Sandra", this.signatureText(1)],
        ["品名确定", `${this.fieldValue("cnName") || "中文品名待填写"} / ${this.fieldValue("enName") || "英文品名待填写"}`, "Sandra", this.signatureText(2)],
        ["规格书编写", `Datasheet：${this.fieldValue("datasheetLink") || "待填写"}`, "Datasheet Team", this.signatureText(4)],
        ["市场宣发", `素材归档：${this.fieldValue("campaignLink") || "待填写"}`, "市场宣发组", this.signatureText(6)]
      ];
    }
  },
  watch: {
    steps: {
      deep: true,
      handler(steps) {
        const activeStepId = this.currentStep?.id;
        this.localSteps = JSON.parse(JSON.stringify(steps));
        const nextIndex = this.localSteps.findIndex(step => step.id === activeStepId);
        this.activeIndex = nextIndex >= 0 ? nextIndex : Math.max(0, this.localSteps.findIndex(step => step.status === "current"));
      }
    },
    instance: {
      deep: true,
      handler(instance) {
        this.draftName = instance.name;
        this.cloudPath = instance.cloudPath || "";
        this.draftCloudPath = instance.cloudPath || "";
      }
    },
    currentStep: {
      immediate: true,
      handler(step) {
        if (!step) return;
        this.assignMode = this.groups[step.owner] ? "group" : "user";
        this.assignee = step.owner;
      }
    }
  },
  methods: {
    isDone(step) { return step.status === "done"; },
    stepBadge(step) { return this.isDone(step) ? "已完成" : step.status === "current" ? "进行中" : "待开始"; },
    fieldValue(key) {
      const labelMap = {
        pn: "PN",
        cnName: "中文品名",
        enName: "英文品名",
        datasheetLink: "Datasheet 链接",
        campaignLink: "素材归档路径"
      };
      for (const step of this.localSteps) {
        const field = step.fields.find(item => item.key === key || item.id === key || item.label === labelMap[key]);
        if (field) return field.value;
      }
      return "";
    },
    signatureText(index) {
      const step = this.localSteps[index];
      if (!step) return "待签";
      if (!step.signatures.length && step.tasks?.some(task => task.status === "done")) {
        const allDone = step.tasks.every(task => task.status === "done");
        return step.rule === "all" && !allDone ? "待签" : "已签";
      }
      if (!step.signatures.length) return "待签";
      return step.signatures.length > 1 ? `${step.signatures.length} 人` : "已签";
    },
    nowText() {
      const pad = value => String(value).padStart(2, "0");
      const now = new Date();
      return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
    },
    editMeta() {
      this.draftName = this.instance.name;
      this.draftCloudPath = this.cloudPath;
      this.editingMeta = true;
    },
    saveMeta() {
      this.$emit("update-instance", { id: this.instance.id, name: this.draftName || this.instance.name, cloudPath: this.draftCloudPath });
      this.cloudPath = this.draftCloudPath;
      this.editingMeta = false;
    },
    applyRemoteInstance(instance) {
      if (instance?.steps?.length) {
        const currentId = instance.currentStepId || this.currentStep?.id;
        this.localSteps = JSON.parse(JSON.stringify(instance.steps));
        const nextIndex = this.localSteps.findIndex(step => step.id === currentId);
        this.activeIndex = nextIndex >= 0 ? nextIndex : Math.max(0, this.localSteps.findIndex(step => step.status === "current"));
      }
      if (instance) this.$emit("instance-updated", instance);
    },
    async persistCurrentFields() {
      if (!this.canEditCurrentStep) {
        this.$message.warning("当前任务没有分配给你，不能填写这个步骤。");
        return;
      }
      if (!this.currentStep?.id || String(this.instance.id).startsWith("new-")) return;
      const values = {};
      for (const field of this.currentStep.fields || []) {
        values[field.id] = field.value || "";
      }
      try {
        const instance = await updateInstanceStepFields(this.instance.id, this.currentStep.id, values);
        this.applyRemoteInstance(instance);
      } catch (error) {
        this.$message.error(error.message || "步骤填写内容保存失败。请联系开发人员/管理员。");
      }
    },
    refreshAssignee() {
      this.assignee = this.assigneeOptions[0] || "";
    },
    async applyAssignment() {
      if (!this.canEditCurrentStep) {
        this.$message.warning("当前任务没有分配给你，不能调整这个步骤。");
        return;
      }
      const step = this.currentStep;
      const assignees = this.assignMode === "group" ? this.groups[this.assignee].slice() : [this.assignee];
      if (step.id && !String(this.instance.id).startsWith("new-")) {
        try {
          const instance = await updateInstanceStepAssignment(this.instance.id, step.id, { assignees, rule: step.rule });
          this.applyRemoteInstance(instance);
          this.events.push({ title: "责任分配", text: `任务已调整为 ${this.assignee}，完成规则已更新。` });
          this.$message.success("责任分配已保存");
        } catch (error) {
          this.$message.error(error.message || "责任分配保存失败。请联系开发人员/管理员。");
        }
        return;
      }
      step.owner = this.assignee;
      step.assignees = assignees;
      step.tasks = this.assignMode === "group"
        ? assignees.map(owner => ({ title: `${step.name}确认`, owner, status: "pending", note: "重新分配后生成的会签任务" }))
        : [];
      this.events.push({ title: "责任分配", text: `任务已调整为 ${this.assignee}，完成规则已更新。` });
      this.$message.success("责任分配已应用");
    },
    async completeTask(index) {
      const task = this.currentStep.tasks[index];
      if (!this.taskCanComplete(task)) {
        this.$message.warning("当前任务没有分配给你，不能完成这个任务。");
        return;
      }
      if (this.hasMissingRequired) {
        this.$message.warning(`请先填写必填项：${this.missingRequiredLabels.join("、")}`);
        return;
      }
      if (task.id && !String(this.instance.id).startsWith("new-")) {
        try {
          const instance = await completeInstanceTask(this.instance.id, task.id);
          this.applyRemoteInstance(instance);
          this.events.push({ title: "子任务完成", text: `${task.owner} 完成了 ${this.currentStep.name} 下的“${task.title}”。` });
          return;
        } catch (error) {
          this.$message.error(error.message || "任务完成失败");
          return;
        }
      }
      task.status = "done";
      this.currentStep.signatures.push(`${task.owner} 于 ${this.nowText()} 完成“${task.title}”`);
      this.events.push({ title: "子任务完成", text: `${task.owner} 完成了 ${this.currentStep.name} 下的“${task.title}”。` });
      if (this.currentStep.rule === "any" || this.currentStep.tasks.every(item => item.status === "done")) await this.completeCurrentStep();
    },
    async completeCurrentStep() {
      if (!this.canEditCurrentStep) {
        this.$message.warning("当前任务没有分配给你，不能完成这个步骤。");
        return;
      }
      if (this.hasMissingRequired) {
        this.$message.warning(`请先填写必填项：${this.missingRequiredLabels.join("、")}`);
        return;
      }
      if (this.currentStep.tasks.some(task => task.status !== "done")) {
        this.$message.warning("还有子任务未完成。");
        return;
      }
      const completedStepName = this.currentStep.name;
      if (this.currentStep.id && !String(this.instance.id).startsWith("new-")) {
        try {
          const instance = await completeInstanceStep(this.instance.id, this.currentStep.id);
          this.applyRemoteInstance(instance);
          this.events.push({ title: "步骤完成", text: `${completedStepName} 已推进。` });
          return;
        } catch (error) {
          this.$message.error(error.message || "步骤完成失败");
          return;
        }
      }
      this.currentStep.status = "done";
      this.currentStep.signatures.push(`${this.currentStep.owner} 于 ${this.nowText()} 完成“${completedStepName}”`);
      if (this.activeIndex + 1 < this.localSteps.length) {
        this.localSteps[this.activeIndex + 1].status = "current";
        this.activeIndex += 1;
      }
      this.events.push({ title: "步骤完成", text: `${completedStepName} 已推进。` });
    },
    async remind() {
      if (!String(this.instance.id).startsWith("new-")) {
        try {
          await remindInstance(this.instance.id, `请处理“${this.currentStep.name}”`);
        } catch (error) {
          this.$message.error(error.message || "催办失败");
          return;
        }
      }
      this.events.push({ title: "催办提醒", text: `已向 ${this.currentStep.owner} 发送“${this.currentStep.name}”待办提醒。` });
      this.$message.success("催办已记录");
    },
    async saveRevision() {
      if (!this.canEditCurrentStep) {
        this.$message.warning("当前任务没有分配给你，不能保存修订。");
        return;
      }
      if (this.hasMissingRequired) {
        this.$message.warning(`请先填写必填项：${this.missingRequiredLabels.join("、")}`);
        return;
      }
      if (this.currentStep.id && !String(this.instance.id).startsWith("new-")) {
        try {
          const instance = await recordStepRevision(this.instance.id, this.currentStep.id, `${this.currentStep.owner} 修订了“${this.currentStep.name}”`);
          this.applyRemoteInstance(instance);
        } catch (error) {
          this.$message.error(error.message || "修订保存失败。请联系开发人员/管理员。");
          return;
        }
      }
      this.currentStep.signatures.push(`${this.currentStep.owner} 于 ${this.nowText()} 修订了“${this.currentStep.name}”`);
      this.editingDone = false;
      this.events.push({ title: "内容修订", text: `${this.currentStep.name} 已追加修订签名。` });
    },
    taskCanComplete(task) {
      return this.canManageCurrentStep || task?.owner === this.currentUser?.name;
    }
  }
};
</script>
