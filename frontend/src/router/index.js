import Vue from "vue";
import VueRouter from "vue-router";

import { getAuthToken } from "@/api/request.js";

const HomeDashboard = () => import("@/views/dashboard/HomeDashboard.vue");
const LoginView = () => import("@/views/login/LoginView.vue");
const ProcessLayout = () => import("@/views/process/ProcessLayout.vue");
const ProcessCatalog = () => import("@/views/process/ProcessCatalog.vue");
const ProcessDesigner = () => import("@/views/process/ProcessDesigner.vue");
const ProcessDetail = () => import("@/views/process/ProcessDetail.vue");
const ProcessRecords = () => import("@/views/process/ProcessRecords.vue");

Vue.use(VueRouter);

const router = new VueRouter({
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/", name: "home", component: HomeDashboard },
    {
      path: "/process",
      component: ProcessLayout,
      children: [
        { path: "", name: "process-catalog", component: ProcessCatalog },
        { path: "templates/:templateId/records", name: "process-records", component: ProcessRecords },
        { path: "templates/:templateId/designer", name: "process-designer", component: ProcessDesigner },
        { path: "instances/:instanceId", name: "process-detail", component: ProcessDetail }
      ]
    },
    { path: "*", redirect: "/" }
  ]
});

router.beforeEach((to, from, next) => {
  if (to.meta.public) {
    if (to.name === "login" && getAuthToken()) next({ name: "home" });
    else next();
    return;
  }
  if (!getAuthToken()) {
    next({ name: "login" });
    return;
  }
  next();
});

export default router;
