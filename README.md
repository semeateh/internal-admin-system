# internal-admin-system

公司内部管理系统，当前为前后端分离结构，重点模块为流程管理。

## 项目结构

- `frontend/`：Vue 2 + Vite 前端
- `backend/`：Flask 后端
- `docs/`：数据库脚本与项目文档

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

## 前端打包

```powershell
cd frontend
npm run build
```

## 后端启动

```powershell
cd backend
pip install -r requirements.txt
python run.py
```

## 配置说明

- 前端配置样例位于 `frontend/.env*.example`
- 后端配置样例位于 `backend/.env*.example`
- 实际 `.env` 文件继续由本地环境维护，不纳入版本管理

## 流程管理约定

- 接口仍统一使用 `/api/...`
- 权限判断以后端校验为准
- 流程状态、操作日志和数据库结构在本次调整中保持不变
