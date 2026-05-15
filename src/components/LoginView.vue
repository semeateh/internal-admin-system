<template>
  <main class="apple-login">
    <section class="login-panel">
      <div class="login-brand">
        <div class="brand-mark">内</div>
        <h1>内部后台管理系统</h1>
        <p>使用公司账号登录后继续管理流程与任务。</p>
      </div>

      <el-form :model="form" class="login-form" @submit.native.prevent="submit">
        <el-form-item>
          <el-input v-model.trim="form.account" autocomplete="username" placeholder="账号" prefix-icon="el-icon-user" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" autocomplete="current-password" placeholder="密码" prefix-icon="el-icon-lock" show-password />
        </el-form-item>
        <el-button class="login-button" type="primary" :loading="loading" @click="submit">登录</el-button>
      </el-form>
    </section>
  </main>
</template>

<script>
import { login } from "../api/auth.js";
import { setAuthToken } from "../api/request.js";

export default {
  name: "LoginView",
  data() {
    return {
      loading: false,
      form: {
        account: "admin",
        password: ""
      }
    };
  },
  methods: {
    async submit() {
      if (!this.form.account || !this.form.password) {
        this.$message.warning("请输入账号和密码");
        return;
      }
      this.loading = true;
      try {
        const result = await login(this.form);
        setAuthToken(result.token);
        this.$emit("login", result.user);
      } catch (error) {
        this.$message.error(error.message || "登录失败");
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
