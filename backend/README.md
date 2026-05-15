# backend

Flask 后端项目。

## 启动

```powershell
pip install -r requirements.txt
python run.py
```

## 结构

- `app/routes/`：路由层
- `app/services/`：业务逻辑层
- `app/repositories/`：数据访问层
- `app/models/`：领域常量与模型
- `app/schemas/`：响应映射与序列化辅助
- `app/common/`：认证、响应和异常等通用能力
- `migrations/`：数据库迁移
