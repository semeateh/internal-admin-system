<template>
  <div class="app">
    <header v-if="isAuthenticated" class="top-nav">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="nav-item" :class="{ active: isHome }" type="button" @click="openModule('home')">首页</button>
          <div class="nav-dropdown">
            <button class="nav-item" :class="{ active: isProcess }" type="button">管理</button>
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

    <main :class="{ shell: isAuthenticated }">
      <router-view
        :modules="visibleManagementModules"
        :current-user="currentUser"
        @login="handleLogin"
        @open-module="openModule"
      />
    </main>
  </div>
</template>

<script>
import { fetchCurrentUser } from "@/api/auth.js";
import { clearAuthToken, getAuthToken } from "@/api/request.js";
import { managementModules } from "@/data/flow-data.js";
import { hasPermission } from "@/utils/permission.js";

export default {
  name: "App",
  data() {
    return {
      currentUser: {},
      isAuthenticated: Boolean(getAuthToken()),
      managementModules
    };
  },
  computed: {
    currentModule() {
      return this.isProcess ? "flow" : "home";
    },
    isHome() {
      return this.$route.name === "home";
    },
    isProcess() {
      return this.$route.path.startsWith("/process");
    },
    visibleManagementModules() {
      return this.managementModules.filter(module => {
        if (module.id === "home") return true;
        const required = { flow: "flow.instance.view" }[module.id];
        return Boolean(required) && hasPermission(this.currentUser, required);
      });
    }
  },
  async mounted() {
    window.addEventListener("auth-unauthorized", this.handleLogout);
    if (this.isAuthenticated) await this.bootstrapAuthenticatedApp();
  },
  beforeDestroy() {
    window.removeEventListener("auth-unauthorized", this.handleLogout);
  },
  methods: {
    async bootstrapAuthenticatedApp() {
      try {
        this.currentUser = await fetchCurrentUser();
      } catch (_) {
        this.handleLogout();
      }
    },
    handleLogin(user) {
      this.currentUser = user || {};
      this.isAuthenticated = true;
      this.$router.replace({ name: "home" });
    },
    handleLogout() {
      clearAuthToken();
      this.currentUser = {};
      this.isAuthenticated = false;
      if (this.$route.name !== "login") this.$router.replace({ name: "login" });
    },
    openModule(module) {
      if (!this.visibleManagementModules.some(item => item.id === module)) {
        this.$message.warning("当前账号没有该功能权限。");
        return;
      }
      if (module === "flow") this.$router.push({ name: "process-catalog" });
      else this.$router.push({ name: "home" });
    }
  }
};
</script>
