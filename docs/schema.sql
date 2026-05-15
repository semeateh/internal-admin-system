-- 内部后台管理系统数据库建表脚本
-- 适用数据库：MySQL 8.x
--
-- 状态约定：
--   通用启用状态：1 = 启用，0 = 禁用
--   员工状态：1 = 在职，0 = 离职
--   流程模板状态：1 = 可使用，0 = 草稿，-1 = 已废弃
--   流程实例状态：1 = 进行中，0 = 已中断，2 = 已完成
--   流程任务状态：0 = 待处理，1 = 已完成，2 = 已跳过
--   附件类型：1 = 附件，2 = 归档文件

CREATE DATABASE IF NOT EXISTS internal_admin_system
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE internal_admin_system;

-- 建表完成后，可继续执行 docs/seed.sql 初始化默认部门、管理员账号、管理员/员工/开发者角色和基础权限。

-- 部门基础数据。员工、组、流程模板都归属于部门。
CREATE TABLE departments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '部门ID',
  department_name VARCHAR(100) NOT NULL COMMENT '部门名称',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_departments_name (department_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表：维护公司内部部门基础信息';

-- 员工登录与基础资料。password_hash 只存加密后的密码，不存明文。
CREATE TABLE employees (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '员工ID',
  account VARCHAR(80) NOT NULL COMMENT '登录账户',
  password_hash VARCHAR(255) NOT NULL COMMENT '加密后的密码哈希，默认密码123456也必须加密后存储',
  must_change_password TINYINT NOT NULL DEFAULT 1 COMMENT '首次登录后是否必须修改密码：1是，0否',
  employee_name VARCHAR(80) NOT NULL COMMENT '员工姓名',
  gender TINYINT DEFAULT NULL COMMENT '性别：1男，2女，0未知',
  position VARCHAR(100) DEFAULT NULL COMMENT '职位',
  department_id BIGINT UNSIGNED NOT NULL COMMENT '部门ID',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1在职，0离职',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_employees_account (account),
  KEY idx_employees_department (department_id),
  CONSTRAINT fk_employees_department
    FOREIGN KEY (department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表：维护员工账号、部门、职位和登录状态';

-- 角色基础数据，例如管理员、员工、开发者、流程管理员、审批人、只读用户。
CREATE TABLE roles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  role_name VARCHAR(100) NOT NULL COMMENT '角色名称',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_roles_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表：维护系统角色定义';

-- 员工与角色的多对多关系。
CREATE TABLE employee_roles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '员工-角色关系ID',
  employee_id BIGINT UNSIGNED NOT NULL COMMENT '员工ID',
  role_id BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_employee_roles_employee_role (employee_id, role_id),
  KEY idx_employee_roles_role (role_id),
  CONSTRAINT fk_employee_roles_employee
    FOREIGN KEY (employee_id) REFERENCES employees (id),
  CONSTRAINT fk_employee_roles_role
    FOREIGN KEY (role_id) REFERENCES roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工-角色关系表：一个员工可拥有多个角色';

-- 权限基础数据。一个权限代表一个受控菜单、按钮或接口能力。
CREATE TABLE permissions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '权限ID',
  permission_code VARCHAR(100) NOT NULL COMMENT '权限编码，后端鉴权使用',
  permission_name VARCHAR(100) NOT NULL COMMENT '权限名称',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  PRIMARY KEY (id),
  UNIQUE KEY uk_permissions_code (permission_code),
  UNIQUE KEY uk_permissions_name (permission_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表：维护菜单、按钮、接口等权限点';

-- 角色与权限的多对多关系。
CREATE TABLE role_permissions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色-权限关系ID',
  role_id BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
  permission_id BIGINT UNSIGNED NOT NULL COMMENT '权限ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_permissions_role_permission (role_id, permission_id),
  KEY idx_role_permissions_permission (permission_id),
  CONSTRAINT fk_role_permissions_role
    FOREIGN KEY (role_id) REFERENCES roles (id),
  CONSTRAINT fk_role_permissions_permission
    FOREIGN KEY (permission_id) REFERENCES permissions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色-权限关系表：角色拥有哪些权限';

-- 员工组基础数据。组可以作为流程步骤的分配对象，例如 Datasheet Team。
CREATE TABLE employee_groups (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '组ID',
  group_name VARCHAR(100) NOT NULL COMMENT '组名',
  department_id BIGINT UNSIGNED NOT NULL COMMENT '部门ID',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_employee_groups_department_name (department_id, group_name),
  CONSTRAINT fk_employee_groups_department
    FOREIGN KEY (department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组表：维护部门下的协作小组';

-- 员工组成员关系。单独建表后，一个员工可以加入多个组。
CREATE TABLE group_members (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '组-员工关系ID',
  group_id BIGINT UNSIGNED NOT NULL COMMENT '组ID',
  employee_id BIGINT UNSIGNED NOT NULL COMMENT '员工ID',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_group_members_group_employee (group_id, employee_id),
  KEY idx_group_members_employee (employee_id),
  CONSTRAINT fk_group_members_group
    FOREIGN KEY (group_id) REFERENCES employee_groups (id),
  CONSTRAINT fk_group_members_employee
    FOREIGN KEY (employee_id) REFERENCES employees (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组-员工关系表：维护小组成员';

-- 流程模板主表。模板下包含步骤、字段、参与人和版本信息。
-- 版本规则：version_code 为全局唯一版本号，由后端统一生成，例如 20260514001。
-- 发布规则：已发布且已有实例的模板记录不可原地修改步骤、字段、负责人，只能新建版本记录。
CREATE TABLE flow_templates (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '模板ID',
  template_name VARCHAR(150) NOT NULL COMMENT '模板名',
  department_id BIGINT UNSIGNED NOT NULL COMMENT '部门ID',
  status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：1可使用，0草稿，-1已废弃',
  description TEXT DEFAULT NULL COMMENT '模板描述',
  default_owner_id BIGINT UNSIGNED DEFAULT NULL COMMENT '默认负责人，关联员工ID',
  version_code VARCHAR(20) NOT NULL COMMENT '全局唯一版本号，例如20260514001；由后端统一生成',
  is_latest TINYINT NOT NULL DEFAULT 1 COMMENT '是否最新版本：1是，0否',
  notify_type VARCHAR(50) DEFAULT NULL COMMENT '通知方式',
  archive_output_type VARCHAR(50) DEFAULT NULL COMMENT '归档输出方式',
  created_by BIGINT UNSIGNED NOT NULL COMMENT '创建人',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_flow_templates_name_version (template_name, version_code),
  UNIQUE KEY uk_flow_templates_version (version_code),
  KEY idx_flow_templates_department (department_id),
  KEY idx_flow_templates_default_owner (default_owner_id),
  KEY idx_flow_templates_created_by (created_by),
  CONSTRAINT fk_flow_templates_department
    FOREIGN KEY (department_id) REFERENCES departments (id),
  CONSTRAINT fk_flow_templates_default_owner
    FOREIGN KEY (default_owner_id) REFERENCES employees (id),
  CONSTRAINT fk_flow_templates_created_by
    FOREIGN KEY (created_by) REFERENCES employees (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程模板表：维护流程模板基本信息和版本';

-- 流程模板步骤。步骤参与人配置保存在 flow_template_step_assignees 表。
CREATE TABLE flow_template_steps (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '步骤ID',
  template_id BIGINT UNSIGNED NOT NULL COMMENT '所属模板ID',
  step_no INT NOT NULL COMMENT '步骤序号',
  step_name VARCHAR(150) NOT NULL COMMENT '步骤名称',
  complete_rule VARCHAR(30) NOT NULL DEFAULT 'owner' COMMENT '完成规则：owner主负责人完成，any任一人完成，all全部完成',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_flow_template_steps_template_no (template_id, step_no),
  KEY idx_flow_template_steps_template (template_id),
  CONSTRAINT fk_flow_template_steps_template
    FOREIGN KEY (template_id) REFERENCES flow_templates (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板步骤表：维护模板中的步骤顺序和完成规则';

-- 步骤参与人配置。assignee_id 根据 assignee_type 指向不同业务表。
CREATE TABLE flow_template_step_assignees (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '步骤参与人ID',
  template_step_id BIGINT UNSIGNED NOT NULL COMMENT '模板步骤ID',
  assignee_type VARCHAR(30) NOT NULL COMMENT '分配对象类型：employee员工、group组、role角色、department部门',
  assignee_id BIGINT UNSIGNED NOT NULL COMMENT '分配对象ID；根据assignee_type分别关联员工、组、角色或部门',
  sort_no INT NOT NULL DEFAULT 1 COMMENT '排序',
  PRIMARY KEY (id),
  UNIQUE KEY uk_step_assignees_step_type_id (template_step_id, assignee_type, assignee_id),
  KEY idx_step_assignees_step (template_step_id),
  CONSTRAINT fk_step_assignees_step
    FOREIGN KEY (template_step_id) REFERENCES flow_template_steps (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='步骤参与人表：配置模板步骤由谁处理';

-- 可复用字段定义。一个字段可以被多个模板步骤使用。
CREATE TABLE flow_fields (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '字段ID',
  field_name VARCHAR(120) NOT NULL COMMENT '字段名',
  field_type VARCHAR(30) NOT NULL COMMENT '类型：text、textarea、number、date、select、radio、checkbox、file',
  required TINYINT NOT NULL DEFAULT 0 COMMENT '是否必填：1是，0否',
  options_json JSON DEFAULT NULL COMMENT '下拉或选项配置JSON；select/radio/checkbox等类型使用',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  KEY idx_flow_fields_name (field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='步骤字段表：维护可复用的表单字段定义';

-- 模板步骤与字段的关系。字段在某个步骤里的必填、默认值和排序配置保存在这里。
CREATE TABLE flow_template_step_fields (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '步骤-字段关系ID',
  template_step_id BIGINT UNSIGNED NOT NULL COMMENT '步骤ID',
  field_id BIGINT UNSIGNED NOT NULL COMMENT '字段ID',
  sort_no INT NOT NULL DEFAULT 1 COMMENT '字段排序',
  required_override TINYINT DEFAULT NULL COMMENT '是否必填覆盖：1是，0否，NULL使用字段默认值',
  default_value TEXT DEFAULT NULL COMMENT '默认值',
  PRIMARY KEY (id),
  UNIQUE KEY uk_step_fields_step_field (template_step_id, field_id),
  UNIQUE KEY uk_step_fields_step_sort (template_step_id, sort_no),
  KEY idx_step_fields_field (field_id),
  CONSTRAINT fk_step_fields_step
    FOREIGN KEY (template_step_id) REFERENCES flow_template_steps (id),
  CONSTRAINT fk_step_fields_field
    FOREIGN KEY (field_id) REFERENCES flow_fields (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='步骤-字段关系表：配置每个步骤包含哪些字段';

-- 流程实例主表。用户基于模板发起流程时生成一条实例记录。
-- 实例只关联创建时的模板版本记录；模板后续修改必须生成新的 flow_templates.id，不影响旧实例。
CREATE TABLE flow_instances (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '实例ID',
  template_id BIGINT UNSIGNED NOT NULL COMMENT '模板ID',
  instance_name VARCHAR(180) NOT NULL COMMENT '实例名称',
  initiator_id BIGINT UNSIGNED NOT NULL COMMENT '发起人',
  current_step_id BIGINT UNSIGNED DEFAULT NULL COMMENT '当前步骤ID',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1进行中，0已中断，2已完成',
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  completed_at DATETIME DEFAULT NULL COMMENT '完成时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  KEY idx_flow_instances_template (template_id),
  KEY idx_flow_instances_initiator (initiator_id),
  KEY idx_flow_instances_current_step (current_step_id),
  KEY idx_flow_instances_status (status),
  CONSTRAINT fk_flow_instances_template
    FOREIGN KEY (template_id) REFERENCES flow_templates (id),
  CONSTRAINT fk_flow_instances_initiator
    FOREIGN KEY (initiator_id) REFERENCES employees (id),
  CONSTRAINT fk_flow_instances_current_step
    FOREIGN KEY (current_step_id) REFERENCES flow_template_steps (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程实例表：记录一次真实发起的流程';

-- 流程运行时任务。根据模板步骤参与人生成，用于待办列表和完成状态追踪。
-- 发起实例时，后端根据模板步骤的 assignee_type 联查员工、组、角色、部门，展开为具体员工后写入本表。
CREATE TABLE flow_instance_tasks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '实例任务ID',
  instance_id BIGINT UNSIGNED NOT NULL COMMENT '实例ID',
  template_step_id BIGINT UNSIGNED NOT NULL COMMENT '步骤ID',
  assignee_id BIGINT UNSIGNED NOT NULL COMMENT '处理人ID',
  status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0待处理，1已完成，2已跳过',
  completed_at DATETIME DEFAULT NULL COMMENT '完成时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_instance_tasks_instance_step_assignee (instance_id, template_step_id, assignee_id),
  KEY idx_instance_tasks_assignee_status (assignee_id, status),
  KEY idx_instance_tasks_step (template_step_id),
  CONSTRAINT fk_instance_tasks_instance
    FOREIGN KEY (instance_id) REFERENCES flow_instances (id),
  CONSTRAINT fk_instance_tasks_step
    FOREIGN KEY (template_step_id) REFERENCES flow_template_steps (id),
  CONSTRAINT fk_instance_tasks_assignee
    FOREIGN KEY (assignee_id) REFERENCES employees (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实例任务表：记录每个流程实例步骤的实际待办';

-- 流程运行时字段值。保存流程实例中用户实际填写的表单内容。
CREATE TABLE flow_instance_field_values (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '实例详情ID',
  instance_id BIGINT UNSIGNED NOT NULL COMMENT '实例ID',
  field_id BIGINT UNSIGNED NOT NULL COMMENT '字段ID',
  template_step_id BIGINT UNSIGNED NOT NULL COMMENT '步骤ID',
  field_value TEXT DEFAULT NULL COMMENT '字段值',
  updated_by BIGINT UNSIGNED DEFAULT NULL COMMENT '更新人',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_instance_field_values_instance_step_field (instance_id, template_step_id, field_id),
  KEY idx_instance_field_values_field (field_id),
  KEY idx_instance_field_values_updated_by (updated_by),
  CONSTRAINT fk_instance_field_values_instance
    FOREIGN KEY (instance_id) REFERENCES flow_instances (id),
  CONSTRAINT fk_instance_field_values_field
    FOREIGN KEY (field_id) REFERENCES flow_fields (id),
  CONSTRAINT fk_instance_field_values_step
    FOREIGN KEY (template_step_id) REFERENCES flow_template_steps (id),
  CONSTRAINT fk_instance_field_values_updated_by
    FOREIGN KEY (updated_by) REFERENCES employees (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实例详情表：保存流程实例中每个步骤字段的填写值';

-- 审计日志。可记录流程实例操作，也可通过 target_type 记录模板、用户、角色等对象变更。
CREATE TABLE operation_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '操作日志ID',
  action VARCHAR(100) NOT NULL COMMENT '操作',
  operator_id BIGINT UNSIGNED NOT NULL COMMENT '操作人',
  detail TEXT DEFAULT NULL COMMENT '操作详情',
  before_json JSON DEFAULT NULL COMMENT '操作前JSON',
  after_json JSON DEFAULT NULL COMMENT '操作后JSON',
  instance_id BIGINT UNSIGNED DEFAULT NULL COMMENT '实例ID',
  target_type VARCHAR(50) DEFAULT NULL COMMENT '操作对象类型，例如flow_instance、flow_template、employee、role',
  target_id BIGINT UNSIGNED DEFAULT NULL COMMENT '操作对象ID；与target_type配合定位被操作记录',
  operated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (id),
  KEY idx_operation_logs_operator (operator_id),
  KEY idx_operation_logs_instance (instance_id),
  KEY idx_operation_logs_target (target_type, target_id),
  CONSTRAINT fk_operation_logs_operator
    FOREIGN KEY (operator_id) REFERENCES employees (id),
  CONSTRAINT fk_operation_logs_instance
    FOREIGN KEY (instance_id) REFERENCES flow_instances (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表：记录用户操作和关键数据变更';

-- 文件附件。保存流程中上传的附件，以及流程完成后生成的归档文件。
CREATE TABLE attachments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '附件ID',
  instance_id BIGINT UNSIGNED NOT NULL COMMENT '实例ID',
  template_step_id BIGINT UNSIGNED DEFAULT NULL COMMENT '步骤ID，可为空',
  field_id BIGINT UNSIGNED DEFAULT NULL COMMENT '字段ID，可为空',
  attachment_type TINYINT NOT NULL COMMENT '类型：1附件，2归档文件',
  original_file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
  stored_file_name VARCHAR(255) NOT NULL COMMENT '存储文件名',
  file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
  uploaded_by BIGINT UNSIGNED NOT NULL COMMENT '上传人',
  uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  PRIMARY KEY (id),
  KEY idx_attachments_instance (instance_id),
  KEY idx_attachments_step (template_step_id),
  KEY idx_attachments_field (field_id),
  KEY idx_attachments_uploaded_by (uploaded_by),
  CONSTRAINT fk_attachments_instance
    FOREIGN KEY (instance_id) REFERENCES flow_instances (id),
  CONSTRAINT fk_attachments_step
    FOREIGN KEY (template_step_id) REFERENCES flow_template_steps (id),
  CONSTRAINT fk_attachments_field
    FOREIGN KEY (field_id) REFERENCES flow_fields (id),
  CONSTRAINT fk_attachments_uploaded_by
    FOREIGN KEY (uploaded_by) REFERENCES employees (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='附件表：保存流程附件和归档文件路径';
