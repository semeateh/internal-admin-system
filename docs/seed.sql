-- 内部后台管理系统初始化数据
-- 执行前请先执行 docs/schema.sql
-- 默认管理员账号：admin
-- 默认管理员密码：123456
-- 注意：这里使用 bcrypt 生成初始化密码哈希。
-- 如需更换默认密码，请使用 tools/password_tool.py 重新生成 hash 后替换 @admin_password_hash。

USE internal_admin_system;

SET @admin_password_hash = '$2b$12$/wpf2.TO0rhCtshGdYi/1unCKPSg8lNWt2sjDvkeL88FfjvgbPI0u';

-- 1. 默认部门
INSERT INTO departments (id, department_name, status)
VALUES
  (1, '市场部', 1)
ON DUPLICATE KEY UPDATE
  department_name = VALUES(department_name),
  status = VALUES(status);

-- 2. 默认角色：管理员、员工
INSERT INTO roles (id, role_name, status)
VALUES
  (1, '管理员', 1),
  (2, '员工', 1)
ON DUPLICATE KEY UPDATE
  role_name = VALUES(role_name),
  status = VALUES(status);

-- 3. 基础权限
INSERT INTO permissions (id, permission_name, status)
VALUES
  (1, '用户管理', 1),
  (2, '角色权限管理', 1),
  (3, '流程模板管理', 1),
  (4, '流程发起', 1),
  (5, '流程处理', 1),
  (6, '流程查看', 1),
  (7, '系统配置', 1)
ON DUPLICATE KEY UPDATE
  permission_name = VALUES(permission_name),
  status = VALUES(status);

-- 4. 管理员拥有全部权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, p.id
FROM permissions p
WHERE p.id IN (1, 2, 3, 4, 5, 6, 7)
ON DUPLICATE KEY UPDATE
  role_id = VALUES(role_id),
  permission_id = VALUES(permission_id);

-- 5. 员工拥有流程相关权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, p.id
FROM permissions p
WHERE p.id IN (4, 5, 6)
ON DUPLICATE KEY UPDATE
  role_id = VALUES(role_id),
  permission_id = VALUES(permission_id);

-- 6. 默认管理员账号
INSERT INTO employees (
  id,
  account,
  password_hash,
  must_change_password,
  employee_name,
  gender,
  position,
  department_id,
  status
)
VALUES (
  1,
  'admin',
  @admin_password_hash,
  0,
  '系统管理员',
  0,
  '系统管理员',
  1,
  1
)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  must_change_password = VALUES(must_change_password),
  employee_name = VALUES(employee_name),
  gender = VALUES(gender),
  position = VALUES(position),
  department_id = VALUES(department_id),
  status = VALUES(status);

-- 7. 默认管理员绑定管理员角色
INSERT INTO employee_roles (employee_id, role_id)
VALUES (1, 1)
ON DUPLICATE KEY UPDATE
  employee_id = VALUES(employee_id),
  role_id = VALUES(role_id);
