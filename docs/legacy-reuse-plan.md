# 旧系统配置复用方案

旧系统路径：

```text
D:\Program Files\git\repository\ownServer
```

新系统优先复用五块能力：

1. 数据库连接配置方式
2. 登录和首次改密逻辑
3. 权限数字兼容
4. 顶部导航和 Element UI 风格
5. 企业微信机器人通知

## 1. 数据库连接配置

旧系统相关文件：

```text
ownServer/.env
ownServer/.env.sample
ownServer/db_connector.py
```

旧系统使用：

```text
DB_HOST
DB_USER
DB_PASSWORD
DB_NAME
SECRET_KEY
```

新系统建议继续使用 `.env` 管理数据库连接。做法是把 `ownServer/.env` 中的数据库主机、账号、密码复制到新系统 `.env`，然后把数据库名改成新后台系统库名：

```text
DB_HOST=从 ownServer/.env 复制
DB_USER=从 ownServer/.env 复制
DB_PASSWORD=从 ownServer/.env 复制
DB_NAME=internal_admin_system
```

如果短期内新旧系统共用同一个 MySQL 服务，`DB_HOST`、`DB_USER`、`DB_PASSWORD` 可以完全沿用旧系统；`DB_NAME` 使用新库：

```text
internal_admin_system
```

实现方式：

- 复用旧系统 `db_connector.py` 的连接池思路。
- 新系统单独建 `database.py` 或 `db_connector.py`。
- 保留连接池、`buffered=True` 游标、连接归还逻辑。
- 不建议直接 import 旧项目的 `db_connector.py`，避免新系统被旧系统目录结构绑定。

## 2. 登录和首次改密

旧系统相关位置：

```text
ownServer/main.py
```

旧系统字段：

```text
webuser.username
webuser.password
webuser.permission
webuser.needResetPwd
```

新系统字段：

```text
employees.account
employees.password_hash
employees.must_change_password
```

映射关系：

| 旧系统 | 新系统 | 说明 |
|---|---|---|
| username | account | 登录账户 |
| password | password_hash | 新系统必须用强哈希，不用 MD5 |
| needResetPwd | must_change_password | 1 表示必须修改密码 |
| permission | roles / permissions | 先兼容，后迁移 |

实现建议：

- 新用户默认密码为 `123456`，但数据库只保存加密 hash。
- 首次登录时，如果 `must_change_password = 1`，跳转修改密码页。
- 修改成功后更新：

```text
must_change_password = 0
password_hash = 新密码hash
```

注意：

- 旧系统使用 `MD5(password)`，新系统不要继续使用 MD5。
- 建议用 `bcrypt`、`argon2` 或 Werkzeug 的 `generate_password_hash`。
- session 中不要保存明文密码。

## 3. 权限数字兼容

旧系统现状：

```text
permission == 1：后台管理员
permission == 2：受限后台账号
permission // 100 == 2：经销商相关账号
permission == 299：公司自营经销商
permission == 0：待审核/无权限
```

新系统已经设计：

```text
roles
permissions
employee_roles
role_permissions
```

建议做一个兼容映射表：

```sql
CREATE TABLE legacy_permission_mappings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '旧权限映射ID',
  legacy_permission INT NOT NULL COMMENT '旧系统 permission 数字',
  role_id BIGINT UNSIGNED NOT NULL COMMENT '新系统角色ID',
  description VARCHAR(200) DEFAULT NULL COMMENT '说明',
  PRIMARY KEY (id),
  UNIQUE KEY uk_legacy_permission_mappings_permission (legacy_permission)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='旧系统权限数字到新系统角色的映射表';
```

示例映射：

| legacy_permission | 新角色 |
|---|---|
| 1 | 管理员 |
| 2 | 受限后台用户 |
| 0 | 待审核用户 |
| 299 | 公司自营经销商 |

这样新系统可以先识别旧权限数字，后续再逐步改为标准角色权限。

## 4. 顶部导航和 Element UI 风格

旧系统相关文件：

```text
ownServer/templates/server/index.html
ownServer/templates/server/*.html
ownServer/static/server/*.css
ownServer/static/release-flow-demo.html
```

已复用内容：

- 顶部导航布局
- 深色导航栏
- hover 下拉菜单
- Element UI 主色 `#409EFF`
- 流程管理原型页

新系统约定：

- 新页面优先使用 Element UI 的视觉规范。
- 按钮使用 `el-button`、`el-button--primary`。
- 输入框使用 `el-input__inner`。
- 标签使用 `el-tag`。
- 卡片使用 `el-card`。

当前文档约定位置：

```text
internal-admin-system/README.md
```

## 5. 企业微信机器人通知

旧系统相关文件：

```text
ownServer/wechatRobot.py
```

可复用点：

- Webhook 发送文本消息
- debug/prod 环境选择不同 webhook
- channel 概念，例如 TEXT、TEST、INSIDE、TOTAL

新系统建议：

新系统 `.env` 中直接复制旧系统企微相关配置，例如：

```text
APP_MODE
WECHAT_WEBHOOK_URL_DEBUG
WECHAT_WEBHOOK_KEY_DEBUG
WECHAT_WEBHOOK_URL_PROD
WECHAT_WEBHOOK_KEY_PROD
```

流程通知建议统一封装：

```python
send_flow_notification(event_type, instance_name, step_name, assignee_name, link)
```

通知事件：

```text
流程创建
节点分配
节点完成
流程中断
流程完成
归档生成
```

注意：

- 旧文件里存在硬编码企业微信凭据，新系统不要继续硬编码。
- 所有 webhook、corp secret、agent id 都应该放到 `.env`。
- 流程系统第一版可以只用 webhook 群通知，不一定马上接企业微信应用消息。

## 推荐落地顺序

1. 新系统建立 `.env` 配置。
2. 复制旧系统连接池思路，创建新系统数据库连接模块。
3. 按 `docs/schema.sql` 建库。
4. 实现登录、首次改密。
5. 建立旧权限数字到新角色的映射。
6. 保留现有导航风格和 Element UI 约定。
7. 封装企业微信流程通知函数。
8. 再开始做流程模板、流程实例、待办任务接口。
