<template>
  <section class="home-view">
    <div class="home-hero">
      <div>
        <span class="eyebrow">管理首页</span>
        <h1>选择要进入的管理模块</h1>
        <p>人员、流程、权限和通知等后台能力从这里进入；新增模块时只需要扩展模块配置。</p>
      </div>
    </div>
    <div class="module-grid">
      <el-card
        v-for="module in visibleModules"
        :key="module.id"
        class="module-card"
        shadow="hover"
        tabindex="0"
        @click.native="$emit('open-module', module.id)"
        @keyup.enter.native="$emit('open-module', module.id)"
      >
        <div class="module-card-top">
          <span class="module-mark">{{ module.title.slice(0, 2) }}</span>
          <el-tag :type="module.id === 'flow' ? 'success' : ''" size="small">{{ module.status }}</el-tag>
        </div>
        <h2>{{ module.title }}</h2>
        <p>{{ module.desc }}</p>
        <div class="module-card-bottom">
          <strong>{{ module.metric }}</strong>
          <el-button type="primary" size="small" @click.stop="$emit('open-module', module.id)">{{ module.action }}</el-button>
        </div>
      </el-card>
    </div>
  </section>
</template>

<script>
export default {
  name: "HomeDashboard",
  props: {
    modules: {
      type: Array,
      required: true
    }
  },
  computed: {
    visibleModules() {
      return this.modules.filter(item => item.id !== "home");
    }
  }
};
</script>
