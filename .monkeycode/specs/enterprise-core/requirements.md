# VMware Cloud Manager - 企业级核心业务需求文档

## 文档信息

| 属性 | 值 |
|------|-----|
| 项目名称 | VMware Cloud Manager |
| 文档类型 | 需求规格说明书 |
| 版本 | v1.0 |
| 日期 | 2026-03-19 |

---

## 1. 多租户与组织隔离

### 1.1 组织管理

| 需求ID | 描述 |
|--------|------|
| ENT-001 | 支持创建多级组织结构（公司→部门→项目组） |
| ENT-002 | 每个组织有独立的管理员 |
| ENT-003 | 组织间资源、VM、存储、网络完全隔离 |
| ENT-004 | 组织可嵌套，最深支持5级 |

### 1.2 资源配额

| 需求ID | 描述 |
|--------|------|
| ENT-010 | CPU配额限制（总核心数） |
| ENT-011 | 内存配额限制（总GB数） |
| ENT-012 | 存储配额限制（总TB数） |
| ENT-013 | VM数量配额限制 |
| ENT-014 | 超配额禁止创建，可配置警告阈值（80%） |
| ENT-015 | 配额使用量实时统计 |

### 1.3 用户与权限

| 需求ID | 描述 |
|--------|------|
| ENT-020 | 用户属于一个或多个组织 |
| ENT-021 | 基于RBAC的权限控制 |
| ENT-022 | 支持角色：超级管理员、组织管理员、普通用户 |
| ENT-023 | 资源操作需校验配额 |

---

## 2. 资源申请与审批流程

### 2.1 申请类型

| 需求ID | 描述 |
|--------|------|
| APP-001 | 虚拟机创建申请 |
| APP-002 | 资源扩容申请（CPU/内存/存储） |
| APP-003 | 快照创建申请 |
| APP-004 | 资源删除申请 |

### 2.2 审批流程

| 需求ID | 描述 |
|--------|------|
| APP-010 | 单人审批 |
| APP-011 | 多级审批（最多5级） |
| APP-012 | 自动审批（配额内自动通过） |
| APP-013 | 审批人委托 |
| APP-014 | 审批超时自动提醒 |
| APP-015 | 审批记录完整审计日志 |

### 2.3 审批状态

```
申请 → 审批中 → 审批通过 → 执行中 → 已完成
                ↓
            审批拒绝
```

---

## 3. 自动化与编排

### 3.1 虚拟机初始化

| 需求ID | 描述 |
|--------|------|
| AUT-001 | Cloud-Init 支持（Linux） |
| AUT-002 | VMware Customization Spec（Windows） |
| AUT-003 | 自定义 IP 地址、网关、DNS |
| AUT-004 | 自定义主机名命名规则 |
| AUT-005 | 自定义 root/Administrator 密码 |
| AUT-006 | 自定义 DNS suffix、domain |
| AUT-007 | 执行自定义脚本 |

### 3.2 定时任务

| 需求ID | 描述 |
|--------|------|
| AUT-010 | 定时开机 |
| AUT-011 | 定时关机 |
| AUT-012 | 定时重启 |
| AUT-013 | 定时清理快照（超过N天） |
| AUT-014 | 定时触发备份 |
| AUT-015 | Cron 表达式支持 |
| AUT-016 | 任务执行历史记录 |

### 3.3 服务目录

| 需求ID | 描述 |
|--------|------|
| AUT-020 | 预设规格模板（小型/中型/大型/巨型） |
| AUT-021 | 自定义规格模板 |
| AUT-022 | 一键部署服务目录中的规格 |
| AUT-023 | 规格可配置 CPU/内存/磁盘/网络 |

---

## 4. 监控与告警

### 4.1 监控指标

| 需求ID | 描述 | 单位 |
|--------|------|------|
| MON-001 | CPU 使用率 | % |
| MON-002 | 内存使用率 | % |
| MON-003 | 磁盘使用率 | % |
| MON-004 | 磁盘 IOPS | ops/s |
| MON-005 | 网络入方向速率 | Mbps |
| MON-006 | 网络出方向速率 | Mbps |
| MON-007 | 虚拟机运行时间 | seconds |
| MON-008 | 主机 CPU/Memory 使用率 | % |
| MON-009 | 集群资源使用率 | % |
| MON-010 | 存储使用率 | % |

### 4.2 告警规则

| 需求ID | 描述 |
|--------|------|
| MON-020 | CPU 使用率 > X% 持续 N 分钟 |
| MON-021 | 内存使用率 > X% |
| MON-022 | 磁盘使用率 > X% |
| MON-023 | 快照超过 N 天 |
| MON-024 | 主机离线 |
| MON-025 | 虚拟机-tools 未运行 |
| MON-026 | 自定义阈值配置 |

### 4.3 告警通知

| 需求ID | 描述 |
|--------|------|
| MON-030 | 企业微信 Webhook |
| MON-031 | 钉钉 Webhook |
| MON-032 | 邮件通知 |
| MON-033 | 短信通知 |
| MON-034 | 平台站内信 |
| MON-035 | 告警收敛（避免轰炸） |
| MON-036 | 告警恢复通知 |

### 4.4 监控数据

| 需求ID | 描述 |
|--------|------|
| MON-040 | 监控数据保留 30 天 |
| MON-041 | 历史曲线图表 |
| MON-042 | 数据导出 Excel/CSV |
| MON-043 | 监控大盘自定义 |

---

## 5. 备份与容灾

### 5.1 备份策略

| 需求ID | 描述 |
|--------|------|
| BAC-001 | 备份类型：全量/增量 |
| BAC-002 | 备份频率：每日/每周/每月 |
| BAC-003 | 保留份数配置 |
| BAC-004 | 备份窗口设置 |
| BAC-005 | 备份目标存储位置 |
| BAC-006 | 虚拟机备份标签/分类 |

### 5.2 备份操作

| 需求ID | 描述 |
|--------|------|
| BAC-010 | 手动触发备份 |
| BAC-011 | 备份任务状态监控 |
| BAC-012 | 备份进度展示 |
| BAC-013 | 备份失败告警 |
| BAC-014 | 备份任务历史 |

### 5.3 备份恢复

| 需求ID | 描述 |
|--------|------|
| BAC-020 | 全量恢复（整机恢复） |
| BAC-021 | 增量恢复 |
| BAC-022 | 异机恢复（恢复到不同主机） |
| BAC-023 | 文件级恢复（单文件恢复） |
| BAC-024 | 恢复前自动创建备份点 |

### 5.4 容灾

| 需求ID | 描述 |
|--------|------|
| BAC-030 | 备份副本异地存储 |
| BAC-031 | RPO/RTO 目标配置 |
| BAC-032 | 容灾演练 |

---

## 6. 数据模型

### 6.1 组织模型

```
Organization
├── id (UUID)
├── name
├── parent_id (自引用)
├── level (层级深度)
├── quota (JSON)
│   ├── cpu_cores
│   ├── memory_gb
│   ├── storage_tb
│   └── vm_count
└── created_at
```

### 6.2 用户-组织关联

```
OrganizationUser
├── organization_id
├── user_id
├── role (admin/member/viewer)
└── is_default_org
```

### 6.3 申请单模型

```
Request
├── id (UUID)
├── type (vm_create/resource_expand/snapshot/backup)
├── organization_id
├── user_id
├── status (pending/approved/rejected/executing/completed/failed)
├── details (JSON)
├── approval_chain (JSON)
└── created_at
```

### 6.4 定时任务模型

```
ScheduledTask
├── id (UUID)
├── organization_id
├── vm_id
├── task_type (start/stop/restart/cleanup_snapshot/backup)
├── cron_expression
├── enabled
├── last_run_at
└── next_run_at
```

### 6.5 监控数据模型

```
MetricSample
├── id
├── entity_type (vm/host/cluster/datastore)
├── entity_id
├── metric_name
├── value
├── timestamp
└── INDEX (entity_id, metric_name, timestamp)
```

### 6.6 告警模型

```
Alert
├── id
├── organization_id
├── rule_id
├── entity_type
├── entity_id
├── severity (warning/critical/info)
├── message
├── status (firing/resolved)
├── triggered_at
├── resolved_at
└── notified_at
```

### 6.7 备份模型

```
BackupJob
├── id
├── organization_id
├── vm_id
├── backup_type (full/incremental)
├── status (pending/running/completed/failed)
├── backup_size_gb
├── started_at
├── completed_at
├── retention_days
└── backup_location
```

---

## 7. API 设计

### 7.1 组织管理

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | /api/organizations | 列表 |
| POST | /api/organizations | 创建 |
| GET | /api/organizations/{id} | 详情 |
| PUT | /api/organizations/{id} | 更新 |
| DELETE | /api/organizations/{id} | 删除 |
| GET | /api/organizations/{id}/quota | 配额使用情况 |
| PUT | /api/organizations/{id}/quota | 更新配额 |

### 7.2 申请审批

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | /api/requests | 列表 |
| POST | /api/requests | 创建申请 |
| GET | /api/requests/{id} | 详情 |
| POST | /api/requests/{id}/approve | 审批通过 |
| POST | /api/requests/{id}/reject | 审批拒绝 |
| POST | /api/requests/{id}/execute | 执行 |

### 7.3 定时任务

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | /api/scheduled-tasks | 列表 |
| POST | /api/scheduled-tasks | 创建 |
| PUT | /api/scheduled-tasks/{id} | 更新 |
| DELETE | /api/scheduled-tasks/{id} | 删除 |
| POST | /api/scheduled-tasks/{id}/run | 立即执行 |
| GET | /api/scheduled-tasks/{id}/history | 执行历史 |

### 7.4 监控告警

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | /api/metrics/{entity_type}/{entity_id} | 指标数据 |
| GET | /api/alerts | 告警列表 |
| POST | /api/alert-rules | 创建告警规则 |
| PUT | /api/alert-rules/{id} | 更新规则 |
| POST | /api/alerts/{id}/acknowledge | 确认告警 |

### 7.5 备份

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | /api/backups | 备份列表 |
| POST | /api/backups | 创建备份任务 |
| POST | /api/backups/{id}/restore | 恢复备份 |
| GET | /api/backup-policies | 备份策略 |
| POST | /api/backup-policies | 创建策略 |

---

## 8. 技术实现

### 8.1 数据库

- PostgreSQL 14+
- TimescaleDB 扩展（监控数据时序存储）
- Redis（缓存、Celery broker）

### 8.2 后台任务

- Celery + Redis
- Celery Beat（定时任务）
- APScheduler（备选）

### 8.3 监控收集

- vSphere Performance Manager API
- 采集间隔：30秒（可配置）
- 数据聚合：5分钟、1小时、1天

### 8.4 备份对接

- vSphere Storage APIs - Data Protection (VADP)
- Chaperone (备选开源方案)
