export const managementModules = [
  { id: "home", title: "管理首页", desc: "集中展示后台管理入口和关键待办。", metric: "6 个模块", status: "总览", action: "返回首页" },
  { id: "people", title: "人员管理", desc: "维护员工、组织、岗位、分组和协作关系。", metric: "7 人", status: "可扩展", action: "进入人员管理" },
  { id: "flow", title: "流程管理", desc: "维护流程模板、流程实例、节点负责人和流转记录。", metric: "10 个模板", status: "已启用", action: "进入流程管理" },
  { id: "template", title: "模板中心", desc: "管理可复用表单、检查清单、通知内容和归档模板。", metric: "建设中", status: "规划中", action: "查看模板中心" },
  { id: "notice", title: "通知配置", desc: "配置企业微信、邮件和站内提醒的触发规则。", metric: "建设中", status: "规划中", action: "查看通知配置" },
  { id: "doc", title: "文档归档", desc: "统一管理流程产物、共享盘路径和归档状态。", metric: "建设中", status: "规划中", action: "查看文档归档" },
  { id: "permission", title: "权限角色", desc: "配置角色、菜单权限、数据权限和审批授权。", metric: "建设中", status: "规划中", action: "查看权限角色" }
];

export const people = ["Zak", "Sandra", "陈辉", "刘依宁", "Gary", "Yolanda", "Jervis"];

export const groups = {
  "Datasheet Team": ["陈辉", "刘依宁", "Gary", "Jervis", "Yolanda", "Sandra", "Zak"],
  "市场宣发组": ["Sandra", "刘依宁", "Zak", "Gary"],
  "价格审批组": ["Yolanda", "Gary", "Zak"]
};

export const templates = [
  { id: "release-market-sales", department: "市场销售部", status: "active", name: "产品 Release 市场销售部流程", owner: "Zak", version: "Ver. 032025", steps: 9, desc: "产品发布前后检查、多人会签、微信通知、最终汇总为查检表。", tags: ["产品发布", "会签", "查检表"] },
  { id: "price-approval", department: "市场销售部", status: "draft", name: "价格调整审批流程", owner: "Yolanda", version: "草稿", steps: 6, desc: "用于国内外价格调整、价格表归档、销售团队通知。", tags: ["价格", "审批"] },
  { id: "custom-order", department: "销售运营", status: "active", name: "定制订单评审流程", owner: "Sandra", version: "Ver. 012026", steps: 7, desc: "定制需求、库存影响、报价、交期和客户确认的协同流程。", tags: ["定制", "订单"] },
  { id: "spec-review", department: "研发测试部", status: "active", name: "规格书数据审查流程", owner: "陈辉", version: "Ver. 052026", steps: 5, desc: "测试数据提交、技术审查、规格书数据确认和归档。", tags: ["规格书", "测试"] },
  { id: "supplier-onboarding", department: "采购部", status: "active", name: "新供应商导入流程", owner: "Gary", version: "Ver. 022026", steps: 8, desc: "供应商资质、样品、价格、合同和系统资料建档。", tags: ["供应商", "采购"] },
  { id: "quality-issue", department: "质量部", status: "active", name: "质量异常处理流程", owner: "陈辉", version: "Ver. 042026", steps: 6, desc: "异常登记、原因分析、纠正措施、复验和关闭确认。", tags: ["质量", "异常"] },
  { id: "campaign-launch", department: "市场销售部", status: "active", name: "市场活动上线流程", owner: "刘依宁", version: "Ver. 052026", steps: 7, desc: "活动素材、目标名单、预算审批、上线检查和效果复盘。", tags: ["市场", "活动"] },
  { id: "sample-loan", department: "销售运营", status: "active", name: "样机借用归还流程", owner: "Jervis", version: "Ver. 032026", steps: 5, desc: "样机申请、审批、出库、归还检查和记录归档。", tags: ["样机", "销售"] },
  { id: "supplier-claim", department: "采购部", status: "draft", name: "供应商索赔流程", owner: "Yolanda", version: "草稿", steps: 6, desc: "质量异常关联供应商索赔、证据上传和财务确认。", tags: ["供应商", "索赔"] },
  { id: "training-cert", department: "研发测试部", status: "active", name: "内部培训认证流程", owner: "刘依宁", version: "Ver. 062026", steps: 4, desc: "培训报名、资料学习、考试记录和证书归档。", tags: ["培训", "认证"] }
];

export const instances = [
  { id: "inst-1", templateId: "release-market-sales", name: "Semea X1 产品发布", department: "市场销售部", status: "active", current: "预确认信息", owner: "Zak", progress: "0/9", updated: "2026-05-11 09:30" },
  { id: "inst-2", templateId: "release-market-sales", name: "Semea M2 海外发布", department: "市场销售部", status: "history", current: "已完成", owner: "Sandra", progress: "9/9", updated: "2026-05-08 17:20" },
  { id: "inst-3", templateId: "custom-order", name: "ACME 定制订单评审", department: "销售运营", status: "active", current: "库存影响", owner: "Sandra", progress: "2/7", updated: "2026-05-10 15:42" },
  { id: "inst-4", templateId: "spec-review", name: "X1 Datasheet 数据审查", department: "研发测试部", status: "active", current: "技术审查", owner: "陈辉", progress: "1/5", updated: "2026-05-09 11:18" }
];

export const steps = [
  {
    id: "precheck",
    name: "预确认信息",
    owner: "Zak",
    status: "current",
    rule: "any",
    desc: "确认销售区域、配套产品、相关产品销售区域是否一致。",
    fields: [
      { key: "area", label: "销售区域", type: "choice", options: ["全球", "仅国内", "仅海外"], value: "全球", required: true },
      { key: "relatedProduct", label: "相关产品名称", type: "text", value: "", required: true }
    ],
    assignees: ["Zak"],
    tasks: [],
    signatures: []
  },
  {
    id: "pn",
    name: "PN 分配",
    owner: "Sandra",
    status: "todo",
    rule: "all",
    desc: "确定产品分类，确认是否新建 PN 分配规则，并填写最终 PN。",
    fields: [
      { key: "productType", label: "产品分类", type: "choice", options: ["新品", "老产品新款"], value: "新品", required: true },
      { key: "newPnRule", label: "是否新建 PN 分配规则", type: "choice", options: ["是", "否"], value: "否", required: true },
      { key: "pn", label: "PN", type: "text", value: "", required: true }
    ],
    assignees: ["Sandra"],
    tasks: [
      { title: "确定产品分类", owner: "Sandra", status: "pending", note: "新品或老产品新款" },
      { title: "填写 PN", owner: "Sandra", status: "pending", note: "确认最终 PN" }
    ],
    signatures: []
  },
  {
    id: "name",
    name: "品名确定",
    owner: "Sandra",
    status: "todo",
    rule: "any",
    desc: "确认命名规则，填写中文品名与英文品名。",
    fields: [
      { key: "newNameRule", label: "是否新建命名规则", type: "choice", options: ["是", "否"], value: "否", required: true },
      { key: "cnName", label: "中文品名", type: "text", value: "", required: true },
      { key: "enName", label: "英文品名", type: "text", value: "", required: true }
    ],
    assignees: ["Sandra"],
    tasks: [],
    signatures: []
  },
  {
    id: "data",
    name: "数据提供",
    owner: "Sandra",
    status: "todo",
    rule: "any",
    desc: "提交图片、参数、认证和卖点数据。",
    fields: [
      { key: "dataLink", label: "资料链接", type: "text", value: "", required: true },
      { key: "dataNote", label: "资料说明", type: "textarea", value: "", required: false }
    ],
    assignees: ["Sandra"],
    tasks: [],
    signatures: []
  },
  {
    id: "datasheet",
    name: "规格书编写",
    owner: "Datasheet Team",
    status: "todo",
    rule: "all",
    desc: "多人共同完成规格书编写和复核。",
    fields: [{ key: "datasheetLink", label: "Datasheet 链接", type: "text", value: "", required: true }],
    assignees: groups["Datasheet Team"],
    tasks: groups["Datasheet Team"].map(owner => ({ title: "规格书确认", owner, status: "pending", note: "会签任务" })),
    signatures: []
  },
  { id: "price", name: "价格确定", owner: "Yolanda", status: "todo", rule: "any", desc: "完成价格表、价格区域和审批记录。", fields: [{ key: "priceLink", label: "价格表链接", type: "text", value: "", required: true }], assignees: ["Yolanda"], tasks: [], signatures: [] },
  { id: "campaign", name: "市场宣发", owner: "市场宣发组", status: "todo", rule: "all", desc: "完成素材归档、推文、海报和内部通知。", fields: [{ key: "campaignLink", label: "素材归档路径", type: "text", value: "", required: true }], assignees: groups["市场宣发组"], tasks: groups["市场宣发组"].map(owner => ({ title: "宣发素材确认", owner, status: "pending", note: "会签任务" })), signatures: [] },
  { id: "website", name: "网站更新", owner: "刘依宁", status: "todo", rule: "any", desc: "更新网站产品页、资料下载和图片。", fields: [{ key: "websiteLink", label: "网站页面链接", type: "text", value: "", required: true }], assignees: ["刘依宁"], tasks: [], signatures: [] },
  { id: "finish", name: "发布完成确认", owner: "Zak", status: "todo", rule: "any", desc: "确认查检表、归档路径和最终通知。", fields: [{ key: "releaseDate", label: "发布日期", type: "date", value: "", required: true }], assignees: ["Zak"], tasks: [], signatures: [] }
];
