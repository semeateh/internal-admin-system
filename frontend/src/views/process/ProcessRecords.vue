<template>
  <main class="records-view">
    <el-card class="panel-card">
      <div slot="header">
        <h2 class="panel-title">{{ template.name }}</h2>
        <p class="panel-subtitle">{{ template.desc || template.description }}</p>
      </div>
      <div class="summary-grid">
        <div class="summary-item"><span>所属部门</span><strong>{{ template.department }}</strong></div>
        <div class="summary-item"><span>默认负责人</span><strong>{{ template.owner }}</strong></div>
        <div class="summary-item"><span>模板版本</span><strong>{{ template.version }}</strong></div>
        <div class="summary-item"><span>步骤数</span><strong>{{ template.steps }} 步</strong></div>
      </div>
    </el-card>

    <section>
      <el-tabs v-model="activeTab" class="record-tabs">
        <el-tab-pane label="正在进行" name="active" />
        <el-tab-pane label="历史流程" name="history" />
      </el-tabs>
      <el-card class="panel-card">
        <el-table class="records-table" :data="rows" size="medium" empty-text="暂无流程。">
          <el-table-column prop="name" label="流程实例" min-width="140" class-name="compact-text-column" show-overflow-tooltip />
          <el-table-column label="状态" width="92">
            <template slot-scope="{ row }">
              <el-tag :type="row.status === 'active' ? '' : 'success'">{{ row.status === "active" ? "进行中" : "已完成" }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="current" label="当前/完成节点" min-width="120" class-name="compact-text-column" show-overflow-tooltip />
          <el-table-column prop="owner" label="负责人" width="96" class-name="compact-text-column" show-overflow-tooltip />
          <el-table-column prop="progress" label="进度" width="76" />
          <el-table-column prop="updated" label="更新时间" width="138" />
          <el-table-column label="操作" width="150">
            <template slot-scope="{ row }">
              <el-button-group class="record-actions">
                <el-button type="primary" size="mini" @click="$emit('open-detail', row.id)">进入</el-button>
                <el-button v-if="canDeleteInstance" type="danger" size="mini" plain @click="$emit('delete-instance', row)">删除</el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </section>
  </main>
</template>

<script>
export default {
  name: "FlowRecords",
  props: {
    template: { type: Object, required: true },
    instances: { type: Array, required: true },
    canDeleteInstance: { type: Boolean, default: false }
  },
  data() {
    return { activeTab: "active" };
  },
  computed: {
    rows() {
      return this.instances.filter(item => item.templateId === this.template.id && item.status === this.activeTab);
    }
  }
};
</script>
