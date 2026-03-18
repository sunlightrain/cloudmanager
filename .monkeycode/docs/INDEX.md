# 云管平台 (Cloud Management Platform)

## 项目概述

VMware vSphere自动化云管平台是一个用于管理虚拟化基础设施的Web平台。通过RESTful API和Web管理界面，实现对VMware vSphere环境中虚拟机的全生命周期管理，包括创建、删除、修改配置、开关机等操作。

## 核心目标

- 提供可视化的VMware vSphere虚拟机管理界面
- 实现虚拟机自动化运维（创建、删除、修改配置）
- 支持批量操作和任务调度
- 提供完整的审计日志和操作记录

## 目标用户

- 运维工程师
- DevOps工程师
- 系统管理员
- 云平台管理人员

## 技术栈

| 层级 | 技术选型 |
|-----|---------|
| 后端框架 | FastAPI (Python 3.10+) |
| 前端框架 | Vue 3 + Element Plus |
| 数据库 | SQLite |
| 认证方式 | Session + Cookie |
| 虚拟化API | pyvmomi (VMware vSphere SDK) |
| 部署方式 | Docker |

## 功能模块

### 1. 认证与授权
- 用户登录/登出
- Session会话管理
- 密码修改

### 2. 资源概览
- vSphere主机/集群状态
- 数据中心资源统计
- 虚拟机数量和使用情况

### 3. 虚拟机管理
- 虚拟机列表与详情
- 创建虚拟机
- 删除虚拟机
- 修改资源配置（CPU、内存、磁盘）
- 开关机操作
- 快照管理

### 4. 任务中心
- 异步任务队列
- 任务状态追踪
- 任务历史记录

### 5. 系统设置
- vSphere连接配置
- 用户管理
- 操作日志审计

## 项目结构

```
cloud-manager/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── requirements.txt
│   └── main.py
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── api/            # API调用
│   │   ├── components/     # 组件
│   │   ├── layouts/        # 布局
│   │   ├── router/         # 路由
│   │   ├── stores/         # 状态管理
│   │   └── views/          # 页面
│   ├── package.json
│   └── vite.config.js
└── docker/                  # Docker配置
    ├── docker-compose.yml
    ├── backend.Dockerfile
    └── frontend.Dockerfile
```

## 版本信息

- 当前版本: 0.1.0 (规划中)
- 创建日期: 2026-03-18

