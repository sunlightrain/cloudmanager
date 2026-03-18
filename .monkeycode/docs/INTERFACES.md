# 接口定义

## 基础信息

- Base URL: `http://localhost:8000/api`
- 认证方式: Session Cookie
- Content-Type: application/json

## 认证接口

### 登录

```
POST /api/auth/login
```

**请求体**:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应 (200)**:

```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "user_id": 1,
    "username": "admin"
  }
}
```

### 登出

```
POST /api/auth/logout
```

**响应 (200)**:

```json
{
  "code": 200,
  "message": "Logout successful"
}
```

### 获取当前用户

```
GET /api/auth/me
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

## 虚拟机管理接口

### 获取虚拟机列表

```
GET /api/vms
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| page | int | 否 | 页码, 默认1 |
| page_size | int | 否 | 每页数量, 默认20 |
| name | string | 否 | 按名称模糊搜索 |
| status | string | 否 | 按状态筛选 |

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "vm_id": "vm-123",
        "name": "web-server-01",
        "status": "poweredOn",
        "cpu": 4,
        "memory_mb": 8192,
        "disk_gb": 100,
        "ip_address": "192.168.1.100",
        "host": "esxi-host-01",
        "created": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

### 获取虚拟机详情

```
GET /api/vms/{vm_id}
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "vm_id": "vm-123",
    "name": "web-server-01",
    "status": "poweredOn",
    "cpu": 4,
    "memory_mb": 8192,
    "disk_gb": 100,
    "ip_address": "192.168.1.100",
    "host": "esxi-host-01",
    "datastore": "datastore1",
    "guest_full_name": "Ubuntu Linux (64-bit)",
    "annotation": "Web服务器",
    "created": "2024-01-15T10:30:00Z"
  }
}
```

### 创建虚拟机

```
POST /api/vms
```

**请求体**:

```json
{
  "name": "new-vm-01",
  "cpu": 2,
  "memory_mb": 4096,
  "disk_gb": 50,
  "network_name": "VM Network",
  "datastore": "datastore1",
  "guest_id": "ubuntu64Guest",
  "annotation": "测试虚拟机"
}
```

**响应 (202)** - 异步任务:

```json
{
  "code": 202,
  "message": "Task created",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
  }
}
```

### 删除虚拟机

```
DELETE /api/vms/{vm_id}
```

**响应 (202)** - 异步任务:

```json
{
  "code": 202,
  "message": "Delete task created",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

### 修改虚拟机配置

```
PATCH /api/vms/{vm_id}
```

**请求体**:

```json
{
  "cpu": 4,
  "memory_mb": 8192
}
```

**响应 (202)** - 异步任务:

```json
{
  "code": 202,
  "message": "Reconfig task created",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440002"
  }
}
```

### 虚拟机电源操作

```
POST /api/vms/{vm_id}/power
```

**请求体**:

```json
{
  "action": "start"  // start, stop, restart, suspend
}
```

**响应 (200)**:

```json
{
  "code": 200,
  "message": "VM powered on successfully"
}
```

## 快照管理接口

### 获取快照列表

```
GET /api/vms/{vm_id}/snapshots
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": [
    {
      "snapshot_id": "snapshot-001",
      "name": "before-update",
      "description": "更新前的快照",
      "created": "2024-01-20T10:00:00Z",
      "size_mb": 10240
    }
  ]
}
```

### 创建快照

```
POST /api/vms/{vm_id}/snapshots
```

**请求体**:

```json
{
  "name": "before-patch",
  "description": "打补丁前快照",
  "memory": true
}
```

**响应 (202)**:

```json
{
  "code": 202,
  "message": "Snapshot created",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440003"
  }
}
```

### 恢复快照

```
POST /api/vms/{vm_id}/snapshots/{snapshot_id}/revert
```

**响应 (202)**:

```json
{
  "code": 202,
  "message": "Snapshot revert task created",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440004"
  }
}
```

### 删除快照

```
DELETE /api/vms/{vm_id}/snapshots/{snapshot_id}
```

**响应 (202)**:

```json
{
  "code": 202,
  "message": "Snapshot deleted",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440005"
  }
}
```

## 任务接口

### 获取任务状态

```
GET /api/tasks/{task_id}
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "task_type": "vm_create",
    "status": "running",
    "result": null,
    "error": null,
    "created_at": "2024-01-20T10:00:00Z",
    "completed_at": null
  }
}
```

### 获取任务列表

```
GET /api/tasks
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| status | string | 否 | pending/running/completed/failed |

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

## 资源概览接口

### 获取主机列表

```
GET /api/hosts
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": [
    {
      "host_id": "host-101",
      "name": "esxi-host-01",
      "status": "connected",
      "cpu_cores": 32,
      "cpu_used_percent": 65,
      "memory_total_gb": 128,
      "memory_used_gb": 72,
      "vm_count": 15
    }
  ]
}
```

### 获取数据中心概览

```
GET /api/overview
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "total_hosts": 5,
    "total_vms": 50,
    "vm_by_status": {
      "poweredOn": 40,
      "poweredOff": 8,
      "suspended": 2
    },
    "total_cpu_cores": 160,
    "total_memory_gb": 640,
    "used_memory_gb": 380,
    "total_storage_tb": 50,
    "used_storage_tb": 25
  }
}
```

## 操作日志接口

### 获取操作日志

```
GET /api/logs
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| user_id | int | 否 | 按用户筛选 |
| operation | string | 否 | 按操作类型筛选 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "username": "admin",
        "operation": "vm_create",
        "target": "new-vm-01",
        "detail": "{\"cpu\": 2, \"memory_mb\": 4096}",
        "created_at": "2024-01-20T10:00:00Z"
      }
    ],
    "total": 1000
  }
}
```

## 系统设置接口

### 获取vSphere连接配置

```
GET /api/settings/vsphere
```

**响应 (200)**:

```json
{
  "code": 200,
  "data": {
    "host": "vcenter.example.com",
    "port": 443,
    "datacenter": "Datacenter",
    "username": "administrator@vsphere.local",
    "connected": true
  }
}
```

### 更新vSphere连接配置

```
PUT /api/settings/vsphere
```

**请求体**:

```json
{
  "host": "vcenter.example.com",
  "port": 443,
  "username": "administrator@vsphere.local",
  "password": "new-password"
}
```

**响应 (200)**:

```json
{
  "code": 200,
  "message": "Configuration updated"
}
```

### 测试vSphere连接

```
POST /api/settings/vsphere/test
```

**响应 (200)**:

```json
{
  "code": 200,
  "message": "Connection successful",
  "data": {
    "version": "8.0.2",
    "build": "12345678"
  }
}
```

## 错误响应格式

所有错误响应遵循以下格式:

```json
{
  "code": 400,
  "message": "Error description",
  "detail": {}
}
```

### 常见错误码

| 状态码 | 说明 |
|-----|-----|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |
| 503 | vSphere连接失败 |

