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

- [ ] 26. 部署验证
  - [ ] 26.1 构建并启动Docker容器

  - [ ] 26.2 验证所有功能正常运行

## 第六阶段：vSphere 核心能力实现

- [x] 30. pyVmomi 连接池管理
  - [x] 30.1 创建 app/core/vsphere/pool.py 连接池
  - [x] 30.2 实现连接复用和自动清理

- [x] 31. vSphere 客户端封装
  - [x] 31.1 创建 app/core/vsphere/client.py 完整封装
  - [x] 31.2 实现数据中心/集群/主机查询
  - [x] 31.3 实现 VM/存储/网络查询
  - [x] 31.4 实现快照管理

- [x] 32. 数据中心层级结构同步
  - [x] 32.1 创建 app/services/datacenter_service.py
  - [x] 32.2 实现树形层级结构 API
  - [x] 32.3 实现数据中心概览

- [x] 33. VM 全生命周期管理
  - [x] 33.1 创建 app/services/vm_service.py
  - [x] 33.2 实现 VM 异步创建/删除/克隆
  - [x] 33.3 实现电源操作（开机/关机/重启/挂起）
  - [x] 33.4 实现资源在线调整（热添加 CPU/内存）

- [x] 34. 存储管理
  - [x] 34.1 创建 app/services/storage_service.py
  - [x] 34.2 实现存储列表和概览

- [x] 35. 网络管理
  - [x] 35.1 创建 app/services/network_service.py
  - [x] 35.2 实现标准/分布式交换机管理
  - [x] 35.3 实现端口组管理

- [x] 36. 集群和迁移服务
  - [x] 36.1 创建 app/services/cluster_service.py
  - [x] 36.2 实现 HA/DRS 配置查看
  - [x] 36.3 实现资源池管理
  - [x] 36.4 实现 vMotion 迁移
  - [x] 36.5 实现 Storage vMotion

- [x] 37. 异步任务系统
  - [x] 37.1 创建 app/tasks/celery_app.py
  - [x] 37.2 实现 VM 异步任务
  - [x] 37.3 实现快照异步任务

- [x] 38. API 路由完善
  - [x] 38.1 更新 /clusters 路由
  - [x] 38.2 更新 /datacenters 路由
  - [x] 38.3 创建 /storage 路由
  - [x] 38.4 创建 /networks 路由
  - [x] 38.5 创建 /migration 路由

## 第七阶段：企业级前端门户

- [x] 40. 统一控制台
  - [x] 40.1 全局资源仪表盘（CPU/内存/存储/VM统计）
  - [x] 40.2 使用率 TOP 排行
  - [x] 40.3 快速操作入口

- [x] 41. 租户自助门户
  - [x] 41.1 创建 TenantPortal.vue 租户页面
  - [x] 41.2 配额管理（VM数量、CPU、内存限制）
  - [x] 41.3 部门 VM 申请/创建/管理
  - [x] 41.4 配额申请流程

- [x] 42. 响应式设计
  - [x] 42.1 侧边栏可折叠
  - [x] 42.2 面包屑导航
  - [x] 42.3 PC/平板适配布局

- [x] 43. 可视化操作
  - [x] 43.1 创建 Topology.vue 拓扑图页面
  - [x] 43.2 数据中心→集群→主机→VM 层级展示
  - [x] 43.3 VMRC 远程控制台集成
  - [x] 43.4 节点详情面板

- [x] 44. 批量操作
  - [x] 44.1 批量开机/关机/重启
  - [x] 44.2 批量删除虚拟机
  - [x] 44.3 批量创建支持

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

