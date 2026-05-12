# internal-admin-system

公司内部后台管理系统原型，当前包含流程管理模块。

## 运行方式

这是一个纯静态原型，可以直接打开 `index.html` 预览，也可以在项目根目录启动本地静态服务：

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

然后访问：

```text
http://127.0.0.1:8000/index.html
```

## 后续模块

- 流程管理
- 流程模板配置
- 通知机器人配置
- 文档归档
- 用户与权限

## UI 约定

后续页面和组件优先使用 Element UI 的视觉规范、主色 `#409EFF` 和组件类名，例如 `el-button`、`el-button--primary`、`el-input__inner`、`el-tag`、`el-card`。自定义样式只用于布局和业务模块差异。
