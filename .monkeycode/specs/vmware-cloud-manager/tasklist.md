# 云管平台实施计划

## 第一阶段：项目基础架构搭建

- [ ] 1. 创建项目目录结构
  - 创建 backend/ 目录及子目录 (app/api, app/core, app/models, app/schemas, app/services, app/utils)
  - 创建 frontend/ 目录及子目录 (src/api, src/components, src/layouts, src/router, src/stores, src/views)
  - 创建 docker/ 目录

- [ ] 2. 初始化后端项目
  - [ ] 2.1 创建 requirements.txt 并添加依赖
    - fastapi, uvicorn, sqlalchemy, pyvmomi, python-multipart, python-jose, passlib, pydantic-settings

  - [ ] 2.2 创建 app/core/config.py 配置文件

  - [ ] 2.3 创建 app/core/database.py 数据库连接

  - [ ] 2.4 创建 app/main.py 应用入口

- [ ] 3. 初始化前端项目
  - [ ] 3.1 创建 package.json 并添加依赖
    - vue, vite, element-plus, vue-router, pinia, axios, @vueuse/core

  - [ ] 3.2 创建 vite.config.ts 配置文件

  - [ ] 3.3 创建 src/main.ts 入口文件

## 第二阶段：后端核心功能实现

- [ ] 4. 数据模型实现
  - [ ] 4.1 创建 app/models/user.py 用户模型

  - [ ] 4.2 创建 app/models/task.py 任务模型

  - [ ] 4.3 创建 app/models/operation_log.py 操作日志模型

  - [ ] 4.4 创建 app/schemas/ 数据验证模型

- [ ] 5. 认证模块实现
  - [ ] 5.1 创建 app/core/security.py 安全工具(密码哈希)

  - [ ] 5.2 创建 app/api/deps.py 依赖注入

  - [ ] 5.3 创建 app/api/routes/auth.py 认证接口

- [ ] 6. vSphere集成
  - [ ] 6.1 创建 app/core/vsphere.py vSphere客户端封装

  - [ ] 6.2 创建 app/services/vsphere_client.py vSphere服务

- [ ] 7. 虚拟机管理模块
  - [ ] 7.1 创建 app/services/vm_service.py 虚拟机服务

  - [ ] 7.2 创建 app/api/routes/vms.py 虚拟机API

  - [ ] 7.3 实现虚拟机列表接口

  - [ ] 7.4 实现虚拟机详情接口

  - [ ] 7.5 实现创建虚拟机接口

  - [ ] 7.6 实现删除虚拟机接口

  - [ ] 7.7 实现修改虚拟机配置接口

  - [ ] 7.8 实现虚拟机电源操作接口

- [ ] 8. 快照管理模块
  - [ ] 8.1 创建 app/api/routes/snapshots.py 快照API

  - [ ] 8.2 实现快照列表接口

  - [ ] 8.3 实现创建快照接口

  - [ ] 8.4 实现恢复快照接口

  - [ ] 8.5 实现删除快照接口

- [ ] 9. 任务管理模块
  - [ ] 9.1 创建 app/services/task_service.py 任务服务

  - [ ] 9.2 创建 app/api/routes/tasks.py 任务API

  - [ ] 9.3 实现任务状态查询接口

  - [ ] 9.4 实现任务列表接口

- [ ] 10. 资源概览模块
  - [ ] 10.1 创建 app/api/routes/hosts.py 主机API

  - [ ] 10.2 实现主机列表接口

  - [ ] 10.3 实现数据中心概览接口

- [ ] 11. 操作日志模块
  - [ ] 11.1 创建 app/api/routes/logs.py 日志API

  - [ ] 11.2 实现操作日志查询接口

- [ ] 12. 系统设置模块
  - [ ] 12.1 创建 app/api/routes/settings.py 设置API

  - [ ] 12.2 实现vSphere配置获取/更新接口

  - [ ] 12.3 实现vSphere连接测试接口

- [ ] 13. 检查点 - 确保后端服务可正常启动

## 第三阶段：前端界面开发

- [ ] 14. 前端基础搭建
  - [ ] 14.1 创建 src/router/index.ts 路由配置

  - [ ] 14.2 创建 src/stores/auth.ts 认证状态管理

  - [ ] 14.3 创建 src/stores/vms.ts 虚拟机状态管理

  - [ ] 14.4 创建 src/api/ 接口调用模块

- [ ] 15. 登录页面
  - [ ] 15.1 创建 src/views/Login.vue 登录页

  - [ ] 15.2 实现登录功能

- [ ] 16. 主布局
  - [ ] 16.1 创建 src/layouts/Default.vue 主布局

  - [ ] 16.2 实现侧边栏导航

  - [ ] 16.3 实现头部用户信息

- [ ] 17. 仪表盘页面
  - [ ] 17.1 创建 src/views/Dashboard.vue 仪表盘

  - [ ] 17.2 实现资源概览卡片

- [ ] 18. 虚拟机列表页面
  - [ ] 18.1 创建 src/views/VmList.vue 虚拟机列表

  - [ ] 18.2 实现虚拟机表格展示

  - [ ] 18.3 实现搜索和筛选功能

  - [ ] 18.4 实现电源操作按钮

- [ ] 19. 虚拟机详情页面
  - [ ] 19.1 创建 src/views/VmDetail.vue 详情页

  - [ ] 19.2 实现虚拟机详细信息展示

- [ ] 20. 创建虚拟机页面
  - [ ] 20.1 创建 src/views/VmCreate.vue 创建页

  - [ ] 20.2 实现表单组件

  - [ ] 20.3 实现创建逻辑

- [ ] 21. 快照管理页面
  - [ ] 21.1 创建 src/views/Snapshots.vue 快照管理

  - [ ] 21.2 实现快照列表展示

  - [ ] 21.3 实现快照操作

- [ ] 22. 任务中心页面
  - [ ] 22.1 创建 src/views/Tasks.vue 任务中心

  - [ ] 22.2 实现任务列表和状态展示

- [ ] 23. 系统设置页面
  - [ ] 23.1 创建 src/views/Settings.vue 设置页面

  - [ ] 23.2 实现vSphere配置管理

- [ ] 24. 检查点 - 确保前后端联调正常

## 第四阶段：Docker部署配置

- [ ] 25. Docker配置
  - [ ] 25.1 创建 docker/docker-compose.yml

  - [ ] 25.2 创建 docker/backend.Dockerfile

  - [ ] 25.3 创建 docker/frontend.Dockerfile

- [ ] 26. 部署验证
  - [ ] 26.1 构建并启动Docker容器

  - [ ] 26.2 验证所有功能正常运行

## 第五阶段：优化与完善

- [ ] 27. 代码优化
  - [ ] 27.1 添加错误处理和日志记录

  - [ ] 27.2 优化数据库查询性能

  - [ ] 27.3 添加请求限流

- [ ] 28. 用户体验优化
  - [ ] 28.1 添加loading状态

  - [ ] 28.2 优化错误提示

  - [ ] 28.3 完善响应式布局

- [ ] 29. 最终检查
  - [ ] 29.1 运行完整功能测试

  - [ ] 29.2 检查代码质量

