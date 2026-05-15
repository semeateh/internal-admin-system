<template>
  <main class="catalog-view">
    <el-card class="panel-card">
      <div slot="header" class="card-header">
        <div>
          <h2 class="panel-title">部门</h2>
          <p class="panel-subtitle">不同部门维护自己的流程模板</p>
        </div>
      </div>
      <el-input v-model="departmentQuery" clearable placeholder="搜索部门" size="medium" />
      <div class="department-list" style="margin-top: 14px;">
        <el-button
          v-for="dept in visibleDepartments"
          :key="dept.name"
          class="department-button"
          :class="{ active: dept.name === selectedDepartment }"
          @click="selectDepartment(dept.name)"
        >
          <span>{{ dept.name }}</span><span>{{ dept.count }}</span>
        </el-button>
      </div>
    </el-card>

    <section class="catalog-main">
      <div class="catalog-toolbar">
        <el-input v-model="templateQuery" clearable placeholder="搜索流程名称、场景或负责人" />
        <el-select v-model="statusFilter" placeholder="全部状态">
          <el-option label="全部状态" value="all" />
          <el-option label="启用中" value="active" />
          <el-option label="草稿" value="draft" />
        </el-select>
      </div>

      <div class="template-grid">
        <el-card
          v-for="template in pagedTemplates"
          :key="template.id"
          class="template-card"
          shadow="hover"
          @click.native="$emit('open-records', template.id)"
        >
          <div class="template-meta">
            <el-tag size="small">{{ template.department }}</el-tag>
            <el-tag size="small" :type="template.status === 'active' ? 'success' : 'warning'">{{ statusText(template.status) }}</el-tag>
          </div>
          <h3>{{ template.name }}</h3>
          <p>{{ template.desc || template.description }}</p>
          <div class="template-meta">
            <el-tag size="small" type="info">{{ template.steps }} 步</el-tag>
            <el-tag size="small" type="info">默认负责人：{{ template.owner }}</el-tag>
            <el-tag size="small" type="info">{{ template.version }}</el-tag>
          </div>
          <div class="template-actions">
            <el-button v-if="canManageTemplate" size="small" @click.stop="$emit('configure-template', template.id)">配置模板</el-button>
            <el-button type="primary" size="small" @click.stop="$emit('open-records', template.id)">查看流程</el-button>
          </div>
        </el-card>
      </div>

      <div class="pagination">
        <el-pagination
          background
          layout="total, prev, pager, next, jumper"
          :total="filteredTemplates.length"
          :page-size="pageSize"
          :current-page.sync="page"
        />
      </div>

      <el-card class="panel-card">
        <div slot="header">
          <h2 class="panel-title">最近流程</h2>
          <p class="panel-subtitle">进入流程后可查看正在进行和历史记录</p>
        </div>
        <el-table :data="recentRows" size="medium">
          <el-table-column prop="name" label="流程实例" min-width="180" />
          <el-table-column prop="department" label="部门" width="110" />
          <el-table-column prop="current" label="当前节点" width="130" />
          <el-table-column prop="owner" label="负责人" width="100" />
          <el-table-column prop="progress" label="进度" width="90" />
          <el-table-column label="操作" width="120">
            <template slot-scope="{ row }">
              <el-button size="mini" @click="$emit('open-records', row.templateId)">查看流程</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </section>
  </main>
</template>

<script>
const ALL_DEPARTMENTS = "全部";
const departmentCollator = new Intl.Collator("zh-Hans-CN", {
  sensitivity: "base",
  numeric: true
});

function getTemplateUpdatedTime(template) {
  const value = template.updatedAt || template.updated || template.updated_at || template.updatedTime || "";
  const time = Date.parse(value);
  return Number.isNaN(time) ? 0 : time;
}

export default {
  name: "FlowCatalog",
  props: {
    templates: { type: Array, required: true },
    instances: { type: Array, required: true },
    canManageTemplate: { type: Boolean, default: false }
  },
  data() {
    return {
      selectedDepartment: ALL_DEPARTMENTS,
      departmentQuery: "",
      templateQuery: "",
      statusFilter: "all",
      page: 1,
      pageSize: 9
    };
  },
  computed: {
    departments() {
      const counts = this.templates.reduce((result, item) => {
        if (!item.department) return result;
        result.set(item.department, (result.get(item.department) || 0) + 1);
        return result;
      }, new Map());
      const names = [...counts.keys()].sort(departmentCollator.compare);
      return [ALL_DEPARTMENTS, ...names].map(name => ({
        name,
        count: name === ALL_DEPARTMENTS ? this.templates.length : counts.get(name)
      }));
    },
    sortedDepartments() {
      return this.departments;
    },
    visibleDepartments() {
      const query = this.departmentQuery.trim().toLowerCase();
      return this.sortedDepartments.filter(item => !query || item.name.toLowerCase().includes(query));
    },
    filteredTemplates() {
      const query = this.templateQuery.trim().toLowerCase();
      return this.templates.filter(item => {
        const deptOk = this.selectedDepartment === ALL_DEPARTMENTS || item.department === this.selectedDepartment;
        const statusOk = this.statusFilter === "all" || item.status === this.statusFilter;
        const description = item.desc || item.description || "";
        const tags = Array.isArray(item.tags) ? item.tags.join(" ") : "";
        const text = `${item.name} ${item.department} ${item.owner} ${description} ${tags}`.toLowerCase();
        return deptOk && statusOk && (!query || text.includes(query));
      });
    },
    sortedFilteredTemplates() {
      return [...this.filteredTemplates].sort((left, right) => {
        const timeDiff = getTemplateUpdatedTime(right) - getTemplateUpdatedTime(left);
        if (timeDiff) return timeDiff;
        return String(right.id).localeCompare(String(left.id), "zh-Hans-CN", { numeric: true });
      });
    },
    pagedTemplates() {
      const start = (this.page - 1) * this.pageSize;
      return this.sortedFilteredTemplates.slice(start, start + this.pageSize);
    },
    recentRows() {
      return this.instances.filter(item => this.selectedDepartment === ALL_DEPARTMENTS || item.department === this.selectedDepartment);
    }
  },
  watch: {
    filteredTemplates() {
      this.page = 1;
    }
  },
  methods: {
    selectDepartment(name) {
      this.selectedDepartment = name;
      this.page = 1;
    },
    statusText(status) {
      return status === "active" ? "启用中" : "草稿";
    }
  }
};
</script>
