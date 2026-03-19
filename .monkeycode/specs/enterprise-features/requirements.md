# 企业级核心业务需求文档

## 1. 多租户与组织隔离

### 1.1 功能描述

支持按部门/项目/子公司创建独立租户组织，实现资源隔离和配额管理。

### 1.2 数据模型

#### 租户 (Tenant)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 租户名称 |
| code | String | 租户编码（唯一） |
| parent_id | Integer | 父租户 ID（支持多级） |
| level | Integer | 层级深度 |
| quota_cpu | Integer | CPU 核心数上限 |
| quota_memory_gb | Integer | 内存上限（GB） |
| quota_storage_gb | Integer | 存储上限（GB） |
| quota_vm_count | Integer | 虚拟机数量上限 |
| is_active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |

#### 租户用户关联 (TenantUser)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| tenant_id | Integer | 租户 ID |
| user_id | Integer | 用户 ID |
| role | String | 角色（owner/admin/member） |

### 1.3 组织层级

```
根租户（公司）
├── 子公司 A
│   ├── 部门 A1
│   └── 部门 A2
├── 子公司 B
│   └── 部门 B1
└── 公共资源
```

### 1.4 资源隔离策略

- 每个租户只能查看和操作本租户及子租户的资源
- 跨租户访问需要超级管理员授权
- 资源（VM/存储/网络）绑定到租户
- API 请求自动注入租户上下文

### 1.5 配额检查

创建资源时自动检查：
- 当前 CPU 使用量 + 申请量 ≤ quota_cpu
- 当前内存使用量 + 申请量 ≤ quota_memory_gb
- 当前存储使用量 + 申请量 ≤ quota_storage_gb
- 当前 VM 数量 + 申请量 ≤ quota_vm_count

超配额返回错误，阻止创建。

---

## 2. 资源申请与审批流程

### 2.1 申请类型

| 类型 | 说明 |
|------|------|
| vm_create | 创建虚拟机 |
| vm_resize | 扩容虚拟机 |
| vm_delete | 删除虚拟机 |
| snapshot_create | 创建快照 |
| snapshot_delete | 删除快照 |
| backup_restore | 备份恢复 |

### 2.2 审批流程

#### 审批模板 (ApprovalTemplate)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 模板名称 |
| request_type | String | 申请类型 |
| steps | JSON | 审批步骤配置 |
| is_auto_approve | Boolean | 是否自动审批 |

#### 审批步骤配置示例
```json
{
  "steps": [
    {"order": 1, "type": "user", "approver": "manager", "name": "部门经理审批"},
    {"order": 2, "type": "role", "approver": "it_admin", "name": "IT 管理员审批"},
    {"order": 3, "type": "auto", "condition": "cpu > 8", "name": "自动判断"}
  ]
}
```

#### 审批记录 (ApprovalRequest)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| request_type | String | 申请类型 |
| tenant_id | Integer | 租户 ID |
| applicant_id | Integer | 申请人 ID |
| resource_type | String | 资源类型 |
| resource_id | String | 资源 ID |
| detail | JSON | 申请详情 |
| status | String | pending/approved/rejected |
| template_id | Integer | 审批模板 ID |
| current_step | Integer | 当前步骤 |
| created_at | DateTime | 创建时间 |

#### 审批记录 (ApprovalRecord)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| request_id | Integer | 申请 ID |
| step_order | Integer | 步骤序号 |
| approver_id | Integer | 审批人 ID |
| action | String | approve/reject |
| comment | String | 审批意见 |
| created_at | DateTime | 审批时间 |

---

## 3. 自动化与编排

### 3.1 服务目录

#### 服务模板 (ServiceTemplate)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 模板名称 |
| category | String | 类别（small/medium/large/custom） |
| cpu | Integer | CPU 核心数 |
| memory_mb | Integer | 内存大小 |
| disk_gb | Integer | 磁盘大小 |
| os_type | String | 操作系统类型 |
| price | Decimal | 价格（可选） |
| is_active | Boolean | 是否启用 |

### 3.2 自动化任务

#### 定时任务 (ScheduledTask)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 任务名称 |
| task_type | String | 类型（vm_power/mnapshot/backup） |
| target_type | String | 目标类型（vm/host/all） |
| target_ids | JSON | 目标 ID 列表 |
| cron_expression | String | Cron 表达式 |
| action_params | JSON | 动作参数 |
| is_active | Boolean | 是否启用 |
| last_run_at | DateTime | 上次运行时间 |
| next_run_at | DateTime | 下次运行时间 |

### 3.3 初始化配置

#### 虚拟机初始化配置 (VMInitConfig)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| vm_id | Integer | 虚拟机 ID |
| hostname | String | 主机名 |
| ip_address | String | IP 地址 |
| subnet_mask | String | 子网掩码 |
| gateway | String | 网关 |
| dns_servers | JSON | DNS 服务器列表 |
| dns_suffix | String | DNS 后缀 |
| custom_script | Text | 自定义脚本 |
| password | String | 初始密码（加密存储） |

---

## 4. 监控与告警

### 4.1 监控指标

| 资源类型 | 指标 |
|----------|------|
| VM | CPU 使用率、内存使用率、磁盘 IO、网络流量、磁盘使用率 |
| Host | CPU 使用率、内存使用率、网络流量、磁盘 IO |
| Cluster | CPU 剩余率、内存剩余率、存储剩余率 |
| Datastore | 容量使用率、IOPS |
| Network | 端口组流量、带宽使用率 |

### 4.2 告警规则

#### 告警规则 (AlertRule)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 规则名称 |
| resource_type | String | 资源类型 |
| metric | String | 指标名称 |
| condition | String | 条件（>/<//>=/<=） |
| threshold | Float | 阈值 |
| duration | Integer | 持续时间（秒） |
| severity | String | 严重程度（info/warning/critical） |
| is_active | Boolean | 是否启用 |

### 4.3 告警记录

#### 告警记录 (Alert)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| rule_id | Integer | 规则 ID |
| tenant_id | Integer | 租户 ID |
| resource_type | String | 资源类型 |
| resource_id | String | 资源 ID |
| metric | String | 指标 |
| value | Float | 当前值 |
| threshold | Float | 阈值 |
| severity | String | 严重程度 |
| status | String | 状态（active/acknowledged/resolved） |
| triggered_at | DateTime | 触发时间 |
| acknowledged_at | DateTime | 确认时间 |
| acknowledged_by | Integer | 确认人 |

### 4.4 通知配置

#### 通知渠道 (NotificationChannel)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 渠道名称 |
| type | String | 类型（webhook/email/sms/wechat/dingtalk） |
| config | JSON | 渠道配置 |
| is_active | Boolean | 是否启用 |

---

## 5. 备份与容灾

### 5.1 备份策略

#### 备份策略 (BackupPolicy)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 策略名称 |
| tenant_id | Integer | 租户 ID |
| target_type | String | 目标类型（vm/datastore） |
| target_ids | JSON | 目标 ID 列表 |
| backup_type | String | 类型（full/incremental） |
| schedule | String | 调度（daily/weekly/monthly） |
| retention_count | Integer | 保留份数 |
| is_active | Boolean | 是否启用 |
| last_backup_at | DateTime | 上次备份时间 |
| next_backup_at | DateTime | 下次备份时间 |

### 5.2 备份记录

#### 备份记录 (BackupJob)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| policy_id | Integer | 策略 ID |
| resource_type | String | 资源类型 |
| resource_id | String | 资源 ID |
| backup_type | String | 备份类型 |
| status | String | 状态（running/completed/failed） |
| size_bytes | Integer | 备份大小 |
| started_at | DateTime | 开始时间 |
| completed_at | DateTime | 完成时间 |
| error_message | String | 错误信息 |

### 5.3 备份恢复

| 恢复类型 | 说明 |
|----------|------|
| 文件恢复 | 从备份中提取单个文件 |
| 整机恢复 | 完全恢复到原 VM |
| 异机恢复 | 恢复到不同的 ESXi 主机 |

---

## 6. API 设计

### 6.1 租户管理

```
GET    /api/tenants              # 获取租户列表
POST   /api/tenants              # 创建租户
GET    /api/tenants/{id}         # 获取租户详情
PUT    /api/tenants/{id}         # 更新租户
DELETE /api/tenants/{id}         # 删除租户
GET    /api/tenants/{id}/quota   # 获取租户配额使用
GET    /api/tenants/{id}/users   # 获取租户用户
POST   /api/tenants/{id}/users   # 添加租户用户
```

### 6.2 审批流程

```
GET    /api/approvals             # 获取申请列表
POST   /api/approvals             # 创建申请
GET    /api/approvals/{id}        # 获取申请详情
POST   /api/approvals/{id}/approve # 审批通过
POST   /api/approvals/{id}/reject  # 审批拒绝
GET    /api/approvals/templates    # 获取审批模板
```

### 6.3 服务目录

```
GET    /api/services              # 获取服务目录
POST   /api/services/orders      # 下单
```

### 6.4 定时任务

```
GET    /api/scheduled-tasks       # 获取定时任务
POST   /api/scheduled-tasks       # 创建定时任务
PUT    /api/scheduled-tasks/{id}   # 更新定时任务
DELETE /api/scheduled-tasks/{id}   # 删除定时任务
POST   /api/scheduled-tasks/{id}/run # 立即执行
```

### 6.5 监控告警

```
GET    /api/metrics/{resource_type}/{resource_id}  # 获取指标
GET    /api/alerts                # 获取告警列表
POST   /api/alerts/{id}/acknowledge # 确认告警
GET    /api/alerts/rules          # 获取告警规则
POST   /api/alerts/rules          # 创建告警规则
```

### 6.6 备份

```
GET    /api/backups               # 获取备份列表
POST   /api/backups               # 创建备份
POST   /api/backups/{id}/restore  # 恢复备份
GET    /api/backups/policies      # 获取备份策略
POST   /api/backups/policies      # 创建备份策略
```
