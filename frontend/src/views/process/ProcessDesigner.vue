<template>
  <main class="template-designer">
    <el-card class="panel-card">
      <div slot="header" class="card-header">
        <div>
          <h2 class="panel-title">模板步骤</h2>
          <p class="panel-subtitle">维护步骤、字段、默认负责人和完成规则</p>
        </div>
        <el-button type="primary" size="mini" icon="el-icon-plus" @click="addStep">新增步骤</el-button>
      </div>
      <div class="designer-step-list">
        <div
          v-for="(step, index) in localSteps"
          :key="step.id"
          class="designer-step"
          :class="{ active: index === activeIndex }"
          @click="activeIndex = index"
        >
          <div>
            <strong>{{ index + 1 }}. {{ step.name }}</strong>
            <span>{{ step.owner }} / {{ step.rule === "all" ? "全部完成" : "任一完成" }}</span>
          </div>
          <div>
            <el-button size="mini" icon="el-icon-top" :disabled="index === 0" @click.stop="moveStep(index, -1)" />
            <el-button size="mini" icon="el-icon-bottom" :disabled="index === localSteps.length - 1" @click.stop="moveStep(index, 1)" />
            <el-button size="mini" icon="el-icon-delete" :disabled="localSteps.length <= 1" @click.stop="deleteStep(index)" />
          </div>
        </div>
      </div>
    </el-card>

    <section class="catalog-main">
      <div class="designer-grid">
        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">模板信息</h2></div>
          <el-form label-position="top" size="medium">
            <el-form-item label="流程名称"><el-input v-model="templateDraft.name" /></el-form-item>
            <el-form-item label="所属部门"><el-input v-model="templateDraft.department" /></el-form-item>
            <el-form-item label="模板状态">
              <el-select v-model="templateDraft.status">
                <el-option label="启用中" value="active" />
                <el-option label="草稿" value="draft" />
              </el-select>
            </el-form-item>
            <el-form-item label="流程说明"><el-input v-model="templateDescription" type="textarea" /></el-form-item>
          </el-form>
        </el-card>

        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">当前步骤</h2></div>
          <el-form v-if="activeStep" label-position="top" size="medium">
            <el-form-item label="步骤名称"><el-input v-model="activeStep.name" /></el-form-item>
            <el-form-item label="默认负责人">
              <el-select v-model="activeStep.owner" filterable>
                <el-option v-for="name in people" :key="name" :label="name" :value="name" />
                <el-option v-for="name in groupNames" :key="name" :label="name" :value="name" />
              </el-select>
            </el-form-item>
            <el-form-item label="完成规则">
              <el-select v-model="activeStep.rule">
                <el-option label="任一人完成" value="any" />
                <el-option label="全部完成" value="all" />
              </el-select>
            </el-form-item>
            <el-form-item label="步骤说明"><el-input v-model="activeStep.desc" type="textarea" /></el-form-item>
          </el-form>
        </el-card>

        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">字段配置</h2></div>
          <div class="template-meta">
            <el-tag v-for="field in activeFields" :key="field.key" :type="field.required ? '' : 'info'">
              {{ field.label }}{{ field.required ? " *" : "" }} / {{ field.type }}
            </el-tag>
          </div>
        </el-card>

        <el-card class="panel-card">
          <div slot="header"><h2 class="panel-title">通知与归档</h2></div>
          <el-form label-position="top" size="medium">
            <el-form-item label="通知方式"><el-select value="wechat"><el-option label="微信机器人" value="wechat" /></el-select></el-form-item>
            <el-form-item label="归档映射"><el-input type="textarea" value="页面填写内容会汇总到 Word 查检表。" /></el-form-item>
          </el-form>
        </el-card>
      </div>
    </section>
  </main>
</template>

<script>
export default {
  name: "TemplateDesigner",
  props: {
    template: { type: Object, required: true },
    steps: { type: Array, required: true },
    people: { type: Array, required: true },
    groups: { type: Object, required: true }
  },
  data() {
    return {
      activeIndex: 0,
      templateDraft: { ...this.template },
      localSteps: JSON.parse(JSON.stringify(this.steps)),
      deletedStepIds: []
    };
  },
  watch: {
    template: {
      deep: true,
      handler(value) {
        this.templateDraft = { ...value };
      }
    },
    steps: {
      deep: true,
      handler(value) {
        this.localSteps = JSON.parse(JSON.stringify(value));
        this.deletedStepIds = [];
        this.activeIndex = 0;
      }
    }
  },
  computed: {
    templateDescription: {
      get() {
        return this.templateDraft.desc || this.templateDraft.description || "";
      },
      set(value) {
        this.$set(this.templateDraft, "desc", value);
        this.$set(this.templateDraft, "description", value);
      }
    },
    activeStep() {
      return this.localSteps[this.activeIndex];
    },
    activeFields() {
      return this.activeStep?.fields || [];
    },
    groupNames() {
      return Object.keys(this.groups);
    }
  },
  methods: {
    addStep() {
      this.localSteps.push({
        id: `custom-${Date.now()}`,
        name: "新增步骤",
        owner: this.people[0],
        rule: "any",
        desc: "请填写步骤说明。",
        fields: [{ key: `field-${Date.now()}`, label: "新增字段", type: "text", value: "", required: false }],
        assignees: [this.people[0]],
        tasks: [],
        signatures: [],
        status: "todo"
      });
      this.activeIndex = this.localSteps.length - 1;
      this.$message.success("已新增步骤");
    },
    moveStep(index, direction) {
      const next = index + direction;
      if (next < 0 || next >= this.localSteps.length) return;
      const copy = this.localSteps.slice();
      const [item] = copy.splice(index, 1);
      copy.splice(next, 0, item);
      this.localSteps = copy;
      this.activeIndex = next;
    },
    deleteStep(index) {
      if (this.localSteps.length <= 1) return;
      const [removed] = this.localSteps.slice(index, index + 1);
      if (/^\d+$/.test(String(removed?.id || ""))) this.deletedStepIds.push(removed.id);
      this.localSteps.splice(index, 1);
      this.activeIndex = Math.min(index, this.localSteps.length - 1);
    },
    buildPayload() {
      return {
        ...this.templateDraft,
        description: this.templateDescription,
        deletedStepIds: this.deletedStepIds,
        steps: this.localSteps.map((step, index) => ({
          ...step,
          stepNo: index + 1,
          assignees: step.assignees?.length ? step.assignees : [step.owner].filter(Boolean),
          fields: (step.fields || []).map((field, fieldIndex) => ({
            ...field,
            key: field.key || field.id || `field-${fieldIndex + 1}`,
            type: field.type === "choice" ? "select" : field.type
          }))
        }))
      };
    }
  }
};
</script>
