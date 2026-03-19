# 云管平台实施计划

## 第一阶段：项目基础架构搭建

- [x] 1. 创建项目目录结构
   - 创建 backend/ 目录及子目录 (app/api, app/core, app/models, app/schemas, app/services, app/utils)
   - 创建 frontend/ 目录及子目录 (src/api, src/components, src/layouts, src/router, src/stores, src/views)
   - 创建 docker/ 目录

- [x] 2. 初始化后端项目
   - [x] 2.1 创建 requirements.txt 并添加依赖
     - fastapi, uvicorn, sqlalchemy, pyvmomi, python-multipart, python-jose, passlib, pydantic-settings

   - [x] 2.2 创建 app/core/config.py 配置文件

   - [x] 2.3 创建 app/core/database.py 数据库连接

   - [x] 2.4 创建 app/main.py 应用入口

- [x] 3. 初始化前端项目
   - [x] 3.1 创建 package.json 并添加依赖
     - vue, vite, element-plus, vue-router, pinia, axios, @vueuse/core

   - [x] 3.2 创建 vite.config.ts 配置文件

   - [x] 3.3 创建 src/main.ts 入口文件

## 第二阶段：后端核心功能实现

- [x] 4. 数据模型实现
   - [x] 4.1 创建 app/models/user.py 用户模型

   - [x] 4.2 创建 app/models/task.py 任务模型

   - [x] 4.3 创建 app/models/operation_log.py 操作日志模型

   - [x] 4.4 创建 app/schemas/ 数据验证模型

- [x] 5. 认证模块实现
   - [x] 5.1 创建 app/core/security.py 安全工具(密码哈希)

   - [x] 5.2 创建 app/api/deps.py 依赖注入

   - [x] 5.3 创建 app/api/routes/auth.py 认证接口

- [x] 6. vSphere集成
   - [x] 6.1 创建 app/core/vsphere.py vSphere客户端封装

   - [x] 6.2 创建 app/services/vsphere_client.py vSphere服务

- [x] 7. 虚拟机管理模块
   - [x] 7.1 创建 app/services/vm_service.py 虚拟机服务

   - [x] 7.2 创建 app/api/routes/vms.py 虚拟机API

   - [x] 7.3 实现虚拟机列表接口

   - [x] 7.4 实现虚拟机详情接口

   - [x] 7.5 实现创建虚拟机接口

   - [x] 7.6 实现删除虚拟机接口

   - [x] 7.7 实现修改虚拟机配置接口

   - [x] 7.8 实现虚拟机电源操作接口

- [x] 8. 快照管理模块
   - [x] 8.1 创建 app/api/routes/snapshots.py 快照API

   - [x] 8.2 实现快照列表接口

   - [x] 8.3 实现创建快照接口

   - [x] 8.4 实现恢复快照接口

   - [x] 8.5 实现删除快照接口

- [x] 9. 任务管理模块
   - [x] 9.1 创建 app/services/task_service.py 任务服务

   - [x] 9.2 创建 app/api/routes/tasks.py 任务API

   - [x] 9.3 实现任务状态查询接口

   - [x] 9.4 实现任务列表接口

- [x] 10. 资源概览模块
   - [x] 10.1 创建 app/api/routes/hosts.py 主机API

   - [x] 10.2 实现主机列表接口

   - [x] 10.3 实现数据中心概览接口

- [x] 11. 操作日志模块
   - [x] 11.1 创建 app/api/routes/logs.py 日志API

   - [x] 11.2 实现操作日志查询接口

- [x] 12. 系统设置模块
   - [x] 12.1 创建 app/api/routes/settings.py 设置API

   - [x] 12.2 实现vSphere配置获取/更新接口

   - [x] 12.3 实现vSphere连接测试接口

- [x] 13. 检查点 - 确保后端服务可正常启动

## 第三阶段：前端界面开发

- [x] 14. 前端基础搭建
   - [x] 14.1 创建 src/router/index.ts 路由配置

   - [x] 14.2 创建 src/stores/auth.ts 认证状态管理

   - [x] 14.3 创建 src/stores/vms.ts 虚拟机状态管理

   - [x] 14.4 创建 src/api/ 接口调用模块

- [x] 15. 登录页面
   - [x] 15.1 创建 src/views/Login.vue 登录页

   - [x] 15.2 实现登录功能

- [x] 16. 主布局
   - [x] 16.1 创建 src/layouts/Default.vue 主布局

   - [x] 16.2 实现侧边栏导航

   - [x] 16.3 实现头部用户信息

- [x] 17. 仪表盘页面
   - [x] 17.1 创建 src/views/Dashboard.vue 仪表盘

   - [x] 17.2 实现资源概览卡片

- [x] 18. 虚拟机列表页面
   - [x] 18.1 创建 src/views/VmList.vue 虚拟机列表

   - [x] 18.2 实现虚拟机表格展示

   - [x] 18.3 实现搜索和筛选功能

   - [x] 18.4 实现电源操作按钮

- [x] 19. 虚拟机详情页面
   - [x] 19.1 创建 src/views/VmDetail.vue 详情页

   - [x] 19.2 实现虚拟机详细信息展示

- [x] 20. 创建虚拟机页面
   - [x] 20.1 创建 src/views/VmCreate.vue 创建页

   - [x] 20.2 实现表单组件

   - [x] 20.3 实现创建逻辑

- [x] 21. 快照管理页面
   - [x] 21.1 创建 src/views/Snapshots.vue 快照管理

   - [x] 21.2 实现快照列表展示

   - [x] 21.3 实现快照操作

- [x] 22. 任务中心页面
   - [x] 22.1 创建 src/views/Tasks.vue 任务中心

   - [x] 22.2 实现任务列表和状态展示

- [x] 23. 系统设置页面
   - [x] 23.1 创建 src/views/Settings.vue 设置页面

   - [x] 23.2 实现vSphere配置管理

- [x] 24. 检查点 - 确保前后端联调正常

## 第四阶段：Docker部署配置

- [x] 25. Docker配置
   - [x] 25.1 创建 docker/docker-compose.yml

   - [x] 25.2 创建 docker/backend.Dockerfile

   - [x] 25.3 创建 docker/frontend.Dockerfile

- [x] 26. 部署验证
   - [x] 26.1 构建并启动Docker容器

   - [x] 26.2 验证所有功能正常运行

## 第五阶段：优化与完善

- [x] 27. 代码优化
   - [x] 27.1 添加错误处理和日志记录

   - [x] 27.2 优化数据库查询性能

   - [x] 27.3 添加请求限流

- [x] 28. 用户体验优化
   - [x] 28.1 添加loading状态

   - [x] 28.2 优化错误提示

   - [x] 28.3 完善响应式布局

- [ ] 29. 最终检查
   - [ ] 29.1 运行完整功能测试

   - [ ] 29.2 检查代码质量

## 安全加固 (本次更新)

- [x] 30. Session 安全机制
   - [x] 30.1 创建 Session 模型存储 token

   - [x] 30.2 使用随机 token 替代用户名作为 session_id

   - [x] 30.3 添加 session 过期机制

- [x] 31. 配置安全
   - [x] 31.1 secret_key 改为随机生成

   - [x] 31.2 debug 模式默认关闭

- [x] 32. 权限控制
   - [x] 32.1 添加 Role 字段到 User 模型

   - [x] 32.2 实现 require_role 依赖注入函数

- [x] 33. 测试覆盖
   - [x] 33.1 添加 pytest 依赖

   - [x] 33.2 创建基础测试用例
