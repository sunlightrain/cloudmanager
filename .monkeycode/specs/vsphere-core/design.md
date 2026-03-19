# VMware Cloud Manager - vSphere 核心能力对接技术设计规格说明书

## 文档信息

| 属性 | 值 |
|------|-----|
| 项目名称 | VMware Cloud Manager |
| 文档类型 | 技术设计规格说明书 |
| 版本 | v1.0 |
| 日期 | 2026-03-19 |
| 状态 | 草稿 |

---

## 1. 概述

### 1.1 设计目标

本文档定义 VMware Cloud Manager 项目中 vSphere 核心能力对接的技术架构和实现方案，确保系统满足以下目标：

- 基于 pyVmomi SDK 实现 vSphere API 全量对接
- 所有操作异步化、任务化，支持进度追踪和取消
- 操作可回滚，保证系统一致性
- 模块化设计，便于扩展和维护

### 1.2 技术栈

| 组件 | 技术选型 | 版本 |
|------|----------|------|
| 编程语言 | Python | 3.9+ |
| vSphere SDK | pyVmomi | 8.0+ |
| Web 框架 | FastAPI | 0.100+ |
| 数据库 | PostgreSQL | 14+ |
| 任务队列 | Celery + Redis | 5.0+ / 7.0+ |
| 缓存 | Redis | 7.0+ |
| ORM | SQLAlchemy | 2.0+ |

### 1.3 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          API Gateway                                │
│                    (FastAPI / Uvicorn)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │  Datacenter │  │   Cluster   │  │    Host     │  │     VM      ││
│  │   Service   │  │   Service   │  │   Service   │  │   Service   ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│
│         │                │                │                │        │
│  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐│
│  │                    pyVmomi Client Pool                        ││
│  │              (Connection Management)                           ││
│  └──────────────────────────┬───────────────────────────────────┘│
│                              │                                     │
├──────────────────────────────┼─────────────────────────────────────┤
│                              │                                     │
│  ┌───────────────────────────┴───────────────────────────────────┐│
│  │                      vCenter Server                            ││
│  │                                                         │      ││
│  │    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────┴──┐   ││
│  │    │ ESXi 1  │    │ ESXi 2  │    │ ESXi N  │    │  Storage │   ││
│  │    └────┬────┘    └────┬────┘    └────┬────┘    └──────────┘   ││
│  └─────────┼──────────────┼─────────────┼─────────────────────────┘│
│            │              │             │                            │
├─────────────┴──────────────┴─────────────┴──────────────────────────┤
│                         Celery Workers                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Task 1  │  │  Task 2  │  │  Task 3  │  │  Task N  │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
├─────────────────────────────────────────────────────────────────────┤
│                         Redis (Broker/Cache)                       │
├─────────────────────────────────────────────────────────────────────┤
│                         PostgreSQL (Metadata)                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 整体架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer (API)            │
│   FastAPI Routes + Pydantic Models + Schemas     │
├─────────────────────────────────────────────────┤
│               Business Logic Layer               │
│   Services + Business Rules + Validation         │
├─────────────────────────────────────────────────┤
│               Integration Layer                  │
│   pyVmomi Client + Connection Pool + Retry      │
├─────────────────────────────────────────────────┤
│               Infrastructure Layer               │
│   Database + Cache + Task Queue + Logging        │
└─────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── vms.py              # VM 相关 API
│   │       ├── hosts.py            # Host 相关 API
│   │       ├── clusters.py         # Cluster 相关 API
│   │       ├── datacenters.py      # Datacenter 相关 API
│   │       ├── storage.py          # Storage 相关 API
│   │       ├── networks.py         # Network 相关 API
│   │       └── tasks.py            # Task 相关 API
│   ├── core/
│   │   ├── config.py               # 配置管理
│   │   ├── security.py             # 安全认证
│   │   └── vsphere/
│   │       ├── client.py           # pyVmomi 客户端
│   │       ├── pool.py             # 连接池管理
│   │       ├── exceptions.py       # 异常定义
│   │       └── utils.py            # 工具函数
│   ├── models/
│   │   ├── vm.py                   # VM 数据模型
│   │   ├── host.py                 # Host 数据模型
│   │   ├── cluster.py              # Cluster 数据模型
│   │   ├── datacenter.py          # Datacenter 数据模型
│   │   ├── storage.py              # Storage 数据模型
│   │   ├── network.py              # Network 数据模型
│   │   └── task.py                 # Task 数据模型
│   ├── schemas/
│   │   ├── vm.py                   # VM 请求/响应模型
│   │   ├── host.py                 # Host 请求/响应模型
│   │   ├── cluster.py              # Cluster 请求/响应模型
│   │   ├── datacenter.py           # Datacenter 请求/响应模型
│   │   ├── storage.py              # Storage 请求/响应模型
│   │   ├── network.py              # Network 请求/响应模型
│   │   └── task.py                 # Task 请求/响应模型
│   ├── services/
│   │   ├── vm_service.py          # VM 业务逻辑
│   │   ├── host_service.py         # Host 业务逻辑
│   │   ├── cluster_service.py      # Cluster 业务逻辑
│   │   ├── datacenter_service.py   # Datacenter 业务逻辑
│   │   ├── storage_service.py     # Storage 业务逻辑
│   │   ├── network_service.py     # Network 业务逻辑
│   │   ├── snapshot_service.py    # Snapshot 业务逻辑
│   │   ├── template_service.py    # Template 业务逻辑
│   │   ├── task_service.py        # Task 业务逻辑
│   │   └── sync_service.py        # 数据同步业务逻辑
│   ├── tasks/
│   │   ├── celery_app.py          # Celery 配置
│   │   ├── vm_tasks.py            # VM 异步任务
│   │   ├── host_tasks.py          # Host 异步任务
│   │   ├── storage_tasks.py       # Storage 异步任务
│   │   ├── network_tasks.py       # Network 异步任务
│   │   └── sync_tasks.py          # 同步异步任务
│   ├── repositories/
│   │   ├── vm_repository.py       # VM 数据访问
│   │   ├── host_repository.py     # Host 数据访问
│   │   └── ...                    # 其他 Repository
│   └── main.py                     # 应用入口
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
└── requirements.txt
```

---

## 3. 核心模块设计

### 3.1 pyVmomi 客户端连接池

#### 3.1.1 连接池管理器

```python
# app/core/vsphere/pool.py
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import threading
from datetime import datetime, timedelta
import ssl

@dataclass
class ConnectionConfig:
    host: str
    port: int = 443
    user: str
    password: str
    ssl_context: Optional[ssl.SSLContext] = None
    connection_timeout: int = 30
    pool_size: int = 10
    max_pool_size: int = 20
    idle_timeout: int = 300

@dataclass
class Connection:
    config: ConnectionConfig
    si: Any  # ServiceInstance
    created_at: datetime
    last_used: datetime
    in_use: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

class VSphereConnectionPool:
    """vSphere 连接池管理器"""
    
    def __init__(self):
        self._pools: Dict[str, List[Connection]] = {}
        self._lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = True
    
    def get_connection(self, config: ConnectionConfig) -> Connection:
        """获取一个连接"""
        pool_key = self._get_pool_key(config)
        
        with self._lock:
            if pool_key not in self._pools:
                self._pools[pool_key] = []
            
            pool = self._pools[pool_key]
            
            # 查找可用连接
            for conn in pool:
                if not conn.in_use and self._is_connection_valid(conn):
                    conn.in_use = True
                    conn.last_used = datetime.now()
                    return conn
            
            # 创建新连接
            if len(pool) < config.max_pool_size:
                conn = self._create_connection(config)
                pool.append(conn)
                return conn
            
            # 等待可用连接
            raise ConnectionPoolExhaustedError(
                f"Connection pool exhausted for {config.host}"
            )
    
    def release_connection(self, conn: Connection):
        """释放连接回连接池"""
        with conn.lock:
            conn.in_use = False
            conn.last_used = datetime.now()
    
    def _create_connection(self, config: ConnectionConfig) -> Connection:
        """创建新连接"""
        from pyVim.connect import SmartConnect, Disconnect
        
        si = SmartConnect(
            host=config.host,
            port=config.port,
            user=config.user,
            pwd=config.password,
            sslContext=config.ssl_context,
            connectionTimeout=config.connection_timeout
        )
        
        return Connection(
            config=config,
            si=si,
            created_at=datetime.now(),
            last_used=datetime.now(),
            in_use=True
        )
    
    def _is_connection_valid(self, conn: Connection) -> bool:
        """检查连接是否有效"""
        if (datetime.now() - conn.last_used).seconds > conn.config.idle_timeout:
            return False
        
        try:
            conn.si.CurrentTime()
            return True
        except Exception:
            return False
    
    def close_all(self):
        """关闭所有连接"""
        self._running = False
        for pool in self._pools.values():
            for conn in pool:
                try:
                    Disconnect(conn.si)
                except Exception:
                    pass
```

#### 3.1.2 pyVmomi 客户端封装

```python
# app/core/vsphere/client.py
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect

from app.core.vsphere.pool import VSphereConnectionPool, ConnectionConfig
from app.core.vsphere.exceptions import (
    VSphereConnectionError,
    VSphereObjectNotFoundError,
    VSphereOperationError
)

logger = logging.getLogger(__name__)

class VSphereClient:
    """vSphere API 客户端封装"""
    
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 443,
        pool: Optional[VSphereConnectionPool] = None
    ):
        self.config = ConnectionConfig(
            host=host,
            user=user,
            password=password,
            port=port
        )
        self._pool = pool or VSphereConnectionPool()
        self._connection: Optional[Connection] = None
    
    def __enter__(self):
        self._connection = self._pool.get_connection(self.config)
        self._si = self._connection.si
        self._content = self._si.RetrieveContent()
        self._root_folder = self._content.rootFolder
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            self._pool.release_connection(self._connection)
    
    @property
    def content(self):
        return self._content
    
    @property
    def root_folder(self):
        return self._root_folder
    
    # ========== 通用查询方法 ==========
    
    def get_obj(self, vim_type: type, name: str) -> Optional[Any]:
        """根据类型和名称查找对象"""
        container = self._root_folder
        container_view = self._view_manager.CreateContainerView(
            container=container,
            type=[vim_type],
            recursive=True
        )
        
        try:
            for obj in container_view.view:
                if obj.name == name:
                    return obj
        finally:
            container_view.Destroy()
        
        return None
    
    def get_all_objs(
        self,
        vim_type: type,
        begin_entity: Optional[Any] = None
    ) -> Dict[str, Any]:
        """获取指定类型的所有对象"""
        if begin_entity is None:
            begin_entity = self._root_folder
        
        container_view = self._view_manager.CreateContainerView(
            container=begin_entity,
            type=[vim_type],
            recursive=True
        )
        
        try:
            return {obj.name: obj for obj in container_view.view}
        finally:
            container_view.Destroy()
    
    # ========== 数据中心相关 ==========
    
    def get_all_datacenters(self) -> List[vim.Datacenter]:
        """获取所有数据中心"""
        return list(self.get_all_objs(vim.Datacenter).values())
    
    def get_datacenter(self, name: str) -> Optional[vim.Datacenter]:
        """获取指定数据中心"""
        return self.get_obj(vim.Datacenter, name)
    
    # ========== 集群相关 ==========
    
    def get_all_clusters(self) -> List[vim.ClusterComputeResource]:
        """获取所有集群"""
        return list(self.get_all_objs(vim.ClusterComputeResource).values())
    
    def get_cluster(self, name: str) -> Optional[vim.ClusterComputeResource]:
        """获取指定集群"""
        return self.get_obj(vim.ClusterComputeResource, name)
    
    def get_cluster_hosts(self, cluster: vim.ClusterComputeResource) -> List[vim.HostSystem]:
        """获取集群下的所有主机"""
        return list(cluster.host)
    
    def get_cluster_resource_summary(
        self,
        cluster: vim.ClusterComputeResource
    ) -> Dict[str, Any]:
        """获取集群资源摘要"""
        summary = cluster.summary
        resource_info = summary.resourcePool
        
        cpu_total = summary.totalCpu
        cpu_used = summary.totalCpu - summary.effectiveCpu
        mem_total = summary.totalMemory
        mem_used = summary.totalMemory - summary.effectiveMemory
        
        return {
            "cpu_total": cpu_total,
            "cpu_used": cpu_used,
            "cpu_free": summary.effectiveCpu,
            "cpu_usage_ratio": cpu_used / cpu_total if cpu_total > 0 else 0,
            "mem_total": mem_total,
            "mem_used": mem_used,
            "mem_free": summary.effectiveMemory,
            "mem_usage_ratio": mem_used / mem_total if mem_total > 0 else 0,
            "host_count": len(cluster.host),
            "vm_count": summary.numHosts * 10,  # 估算
        }
    
    # ========== 主机相关 ==========
    
    def get_all_hosts(self) -> List[vim.HostSystem]:
        """获取所有主机"""
        return list(self.get_all_objs(vim.HostSystem).values())
    
    def get_host(self, name: str) -> Optional[vim.HostSystem]:
        """获取指定主机"""
        return self.get_obj(vim.HostSystem, name)
    
    def get_host_hardware_info(
        self,
        host: vim.HostSystem
    ) -> Dict[str, Any]:
        """获取主机硬件信息"""
        hardware = host.hardware
        cpu_info = hardware.cpuPkg[0] if hardware.cpuPkg else None
        
        return {
            "cpu": {
                "model": cpu_info.name if cpu_info else "Unknown",
                "cores": hardware.cpuInfo.numCpuCores,
                "threads": hardware.cpuInfo.numCpuThreads,
                "hz": hardware.cpuInfo.hz,
                "cpu_count": hardware.cpuInfo.numCpuPackages,
            },
            "memory": {
                "total": hardware.memorySize,
                "used": hardware.memorySize - host.summary.runtime.memoryCapacity,
            },
            "storage": {
                "total": sum(
                    datastore.summary.capacity 
                    for datastore in host.datastore
                ),
                "used": sum(
                    datastore.summary.capacity - datastore.summary.freeSpace
                    for datastore in host.datastore
                ),
            },
            "network": [
                {
                    "name": nic.device.label,
                    "mac": nic.macAddress,
                    "ip": nic.networkProfile.ipAddress[0].ipAddress 
                          if nic.networkProfile and nic.networkProfile.ipAddress 
                          else None,
                }
                for nic in hardware.network
            ],
            "health": {
                "cpu_temperature": self._get_sensor_value(
                    host, "CPU Package"
                ),
                "memory_errors": hardware.memoryErrors,
                "fan_status": self._get_all_fan_status(host),
            }
        }
    
    def get_host_runtime_info(
        self,
        host: vim.HostSystem
    ) -> Dict[str, Any]:
        """获取主机运行时信息"""
        runtime = host.runtime
        
        return {
            "connection_state": str(runtime.connectionState),
            "power_state": str(runtime.powerState),
            "maintenance_mode": runtime.inMaintenanceMode,
            "uptime": runtime.bootTime,
            "standby_mode": runtime.standbyMode,
        }
    
    def get_host_resource_usage(
        self,
        host: vim.HostSystem
    ) -> Dict[str, Any]:
        """获取主机资源使用情况"""
        summary = host.summary
        quickStats = summary.quickStats
        
        return {
            "cpu": {
                "used": quickStats.overallCpuUsage,
                "total": summary.hardware.cpuInfo.hz * summary.hardware.cpuInfo.numCpuCores,
                "usage_ratio": quickStats.overallCpuUsage / (
                    summary.hardware.cpuInfo.hz * summary.hardware.cpuInfo.numCpuCores / 1e9
                ) if summary.hardware.cpuInfo.hz else 0,
            },
            "memory": {
                "used": quickStats.overallMemoryUsage * 1024 * 1024,  # GB to bytes
                "total": summary.hardware.memorySize,
                "usage_ratio": quickStats.overallMemoryUsage * 1024 * 1024 / summary.hardware.memorySize
                               if summary.hardware.memorySize else 0,
            },
        }
    
    # ========== 虚拟机相关 ==========
    
    def get_all_vms(self) -> List[vim.VirtualMachine]:
        """获取所有虚拟机"""
        return list(self.get_all_objs(vim.VirtualMachine).values())
    
    def get_vm(self, name: str) -> Optional[vim.VirtualMachine]:
        """获取指定虚拟机"""
        return self.get_obj(vim.VirtualMachine, name)
    
    def get_vm_by_uuid(self, uuid: str) -> Optional[vim.VirtualMachine]:
        """根据 UUID 获取虚拟机"""
        search_index = self._si.content.searchIndex
        return search_index.FindByUuid(None, uuid, True, True)
    
    def get_vm_summary(
        self,
        vm: vim.VirtualMachine
    ) -> Dict[str, Any]:
        """获取虚拟机摘要信息"""
        summary = vm.summary
        config = summary.config
        
        return {
            "name": config.name,
            "uuid": config.uuid,
            "guest_full_name": config.guestFullName,
            "memory_size": config.memorySizeMB,
            "num_cpu": config.numCpu,
            "disk_capacity": sum(
                disk.capacityInKB * 1024 
                for disk in config.device
                if isinstance(disk, vim.vm.device.VirtualDisk)
            ),
            "ip_address": summary.guest.ipAddress,
            "power_state": str(summary.runtime.powerState),
            "tools_status": str(summary.guest.toolsStatus),
            "tools_version": summary.guest.toolsVersion,
            "host_name": summary.guest.hostName,
        }
    
    def get_vm_snapshot_info(
        self,
        vm: vim.VirtualMachine
    ) -> Dict[str, Any]:
        """获取虚拟机快照信息"""
        if not hasattr(vm, 'snapshot') or not vm.snapshot:
            return {"has_snapshots": False, "snapshots": []}
        
        root_snapshots = vm.snapshot.rootSnapshotList
        
        def parse_snapshot_tree(snap_list: List) -> List[Dict]:
            result = []
            for snap in snap_list:
                result.append({
                    "id": snap.id,
                    "name": snap.name,
                    "description": snap.description,
                    "creation_time": snap.createTime,
                    "state": str(snap.state),
                    "children": parse_snapshot_tree(snap.childSnapshotList) 
                                if snap.childSnapshotList else []
                })
            return result
        
        return {
            "has_snapshots": True,
            "snapshots": parse_snapshot_tree(root_snapshots)
        }
    
    # ========== 存储相关 ==========
    
    def get_all_datastores(self) -> List[vim.Datastore]:
        """获取所有存储"""
        return list(self.get_all_objs(vim.Datastore).values())
    
    def get_datastore(self, name: str) -> Optional[vim.Datastore]:
        """获取指定存储"""
        return self.get_obj(vim.Datastore, name)
    
    def get_datastore_summary(
        self,
        datastore: vim.Datastore
    ) -> Dict[str, Any]:
        """获取存储摘要信息"""
        summary = datastore.summary
        
        return {
            "name": summary.name,
            "capacity": summary.capacity,
            "free_space": summary.freeSpace,
            "used_space": summary.capacity - summary.freeSpace,
            "usage_ratio": (summary.capacity - summary.freeSpace) / summary.capacity
                          if summary.capacity > 0 else 0,
            "type": summary.type,
            "vm_count": summary.vmCount,
            "accessible": summary.accessible,
        }
    
    # ========== 网络相关 ==========
    
    def get_all_networks(self) -> Dict[str, Any]:
        """获取所有网络（标准交换机和分布式交换机）"""
        networks = {}
        
        # 标准交换机
        for network in self.get_all_objs(vim.Network).values():
            networks[network.name] = {
                "type": "standard",
                "obj": network,
                "name": network.name,
            }
        
        # 分布式交换机
        for dvs in self.get_all_objs(vim.dvs.VmwareDistributedVirtualSwitch).values():
            networks[dvs.name] = {
                "type": "distributed",
                "obj": dvs,
                "name": dvs.name,
                "port_group_count": len(dvs.portgroup),
            }
        
        return networks
    
    def get_port_groups(self) -> List[vim.Network]:
        """获取所有端口组"""
        return list(self.get_all_objs(vim.DistributedVirtualPortgroup).values())
    
    # ========== 辅助方法 ==========
    
    def _get_sensor_value(self, host: vim.HostSystem, sensor_name: str) -> Any:
        """获取传感器值"""
        try:
            for sensor in host.hardware.sensor:
                if sensor_name.lower() in sensor.name.lower():
                    return sensor.currentReading
        except Exception:
            pass
        return None
    
    def _get_all_fan_status(self, host: vim.HostSystem) -> List[Dict]:
        """获取所有风扇状态"""
        fans = []
        try:
            for sensor in host.hardware.sensor:
                if "fan" in sensor.name.lower():
                    fans.append({
                        "name": sensor.name,
                        "status": str(sensor.healthState),
                        "current_reading": sensor.currentReading,
                    })
        except Exception:
            pass
        return fans
```

### 3.2 异步任务设计

#### 3.2.1 Celery 配置

```python
# app/tasks/celery_app.py
from celery import Celery
from celery.result import AsyncResult
from typing import Optional, Dict, Any
import json

from app.core.config import settings

celery_app = Celery(
    "vsphere_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
    include=[
        "app.tasks.vm_tasks",
        "app.tasks.host_tasks",
        "app.tasks.storage_tasks",
        "app.tasks.network_tasks",
        "app.tasks.sync_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "app.tasks.vm_tasks.*": {"queue": "vm_operations"},
        "app.tasks.host_tasks.*": {"queue": "host_operations"},
        "app.tasks.storage_tasks.*": {"queue": "storage_operations"},
        "app.tasks.network_tasks.*": {"queue": "network_operations"},
        "app.tasks.sync_tasks.*": {"queue": "sync_operations"},
    },
    task_annotations={
        "*": {
            "rate_limit": "100/m"
        }
    }
)

class TaskResult:
    """任务结果封装"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self._result: Optional[AsyncResult] = None
    
    @property
    def result(self) -> AsyncResult:
        if self._result is None:
            self._result = AsyncResult(self.task_id, app=celery_app)
        return self._result
    
    @property
    def status(self) -> str:
        return self.result.state
    
    @property
    def info(self) -> Optional[Dict[str, Any]]:
        if self.result.ready():
            return self.result.result
        elif self.result.state == "PROGRESS":
            return self.result.info
        return None
    
    @property
    def progress(self) -> Optional[int]:
        if self.result.state == "PROGRESS" and isinstance(self.result.info, dict):
            return self.result.info.get("progress", 0)
        return None
    
    def wait(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        return self.result.get(timeout=timeout)
    
    def revoke(self, terminate: bool = False):
        self.result.revoke(terminate=terminate)
```

#### 3.2.2 虚拟机异步任务

```python
# app/tasks/vm_tasks.py
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.tasks.celery_app import celery_app
from app.core.vsphere.client import VSphereClient
from app.core.vsphere.exceptions import VSphereOperationError
from app.models.task import TaskRecord, TaskStatus

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="vm_tasks.create_vm")
def create_vm_task(
    self,
    vcenter_id: str,
    datacenter_name: str,
    cluster_name: str,
    resource_pool_name: str,
    vm_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建虚拟机任务
    
    Args:
        vcenter_id: vCenter 标识
        datacenter_name: 数据中心名称
        cluster_name: 集群名称
        resource_pool_name: 资源池名称
        vm_config: 虚拟机配置
    
    Returns:
        创建结果，包含虚拟机 MoRef 和名称
    """
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.create",
        status=TaskStatus.PENDING,
        start_time=datetime.now(),
        metadata={
            "vm_name": vm_config.get("name"),
            "vcenter_id": vcenter_id,
        }
    )
    
    try:
        task_record.status = TaskStatus.RUNNING
        task_record.save()
        
        # 更新进度：连接 vCenter
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "step": "connecting_vcenter"}
        )
        
        # 获取 vCenter 连接
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            # 获取目标位置
            datacenter = client.get_datacenter(datacenter_name)
            if not datacenter:
                raise VSphereOperationError(f"Datacenter {datacenter_name} not found")
            
            cluster = client.get_cluster(cluster_name)
            if not cluster:
                raise VSphereOperationError(f"Cluster {cluster_name} not found")
            
            # 获取资源池
            resource_pool = _get_resource_pool(cluster, resource_pool_name)
            
            # 更新进度：准备配置
            self.update_state(
                state="PROGRESS",
                meta={"progress": 30, "step": "preparing_config"}
            )
            
            # 创建虚拟机配置
            vm_folder = datacenter.vmFolder
            vm_create_spec = _build_vm_create_spec(client, vm_config)
            
            # 更新进度：创建虚拟机
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "step": "creating_vm"}
            )
            
            # 执行创建
            task = vm_folder.CreateVM(
                spec=vm_create_spec,
                pool=resource_pool,
                host=None
            )
            
            # 等待任务完成
            result = _wait_for_task(task, timeout=600)
            
            # 获取创建的虚拟机
            vm_name = vm_config.get("name")
            vm = client.get_vm(vm_name)
            
            # 更新进度：完成
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "step": "completed"}
            )
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {
                "vm_moref": str(vm._moId),
                "vm_uuid": vm.summary.config.uuid,
                "vm_name": vm_name,
            }
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to create VM: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        # 执行回滚
        _rollback_create_vm(vcenter_id, vm_config.get("name"))
        
        raise


@celery_app.task(bind=True, name="vm_tasks.power_operation")
def vm_power_operation_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    operation: str  # start, stop, restart, suspend, resume
) -> Dict[str, Any]:
    """虚拟机电源操作任务"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type=f"vm.power.{operation}",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "operation": operation,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            # 执行电源操作
            if operation == "start":
                task = vm.PowerOnVM()
            elif operation == "stop":
                task = vm.PowerOffVM()
            elif operation == "restart":
                vm.PowerOffVM()
                task = vm.PowerOnVM()
            elif operation == "suspend":
                task = vm.SuspendVM()
            elif operation == "resume":
                task = vm.PowerOnVM()
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            result = _wait_for_task(task)
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {"success": True}
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to perform power operation: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise


@celery_app.task(bind=True, name="vm_tasks.resize_resources")
def vm_resize_resources_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    cpu: Optional[int] = None,
    memory_mb: Optional[int] = None,
    disk_size_gb: Optional[int] = None
) -> Dict[str, Any]:
    """虚拟机资源变更任务（在线/离线）"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.resize",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "cpu": cpu,
            "memory_mb": memory_mb,
            "disk_size_gb": disk_size_gb,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            changes = []
            
            # CPU 变更
            if cpu is not None:
                self.update_state(
                    state="PROGRESS",
                    meta={"progress": 25, "step": "resizing_cpu"}
                )
                _resize_cpu(client, vm, cpu)
                changes.append(f"cpu:{vm.config.hardware.numCPU}->{cpu}")
            
            # 内存变更
            if memory_mb is not None:
                self.update_state(
                    state="PROGRESS",
                    meta={"progress": 50, "step": "resizing_memory"}
                )
                _resize_memory(client, vm, memory_mb)
                changes.append(f"memory:{vm.config.hardware.memoryMB}->{memory_mb}")
            
            # 磁盘变更
            if disk_size_gb is not None:
                self.update_state(
                    state="PROGRESS",
                    meta={"progress": 75, "step": "resizing_disk"}
                )
                _resize_disk(client, vm, disk_size_gb)
                changes.append(f"disk:->{disk_size_gb}GB")
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "step": "completed"}
            )
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {
                "changes": changes,
                "new_config": client.get_vm_summary(vm),
            }
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to resize VM resources: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise


@celery_app.task(bind=True, name="vm_tasks.create_snapshot")
def create_snapshot_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    snapshot_name: str,
    description: str = "",
    memory: bool = False,
    quiesce: bool = False
) -> Dict[str, Any]:
    """创建快照任务"""
    # 检查快照数量限制
    snapshot_limit_hours = 72
    
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.snapshot.create",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "snapshot_name": snapshot_name,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            # 检查现有快照
            snapshot_info = client.get_vm_snapshot_info(vm)
            if snapshot_info.get("has_snapshots"):
                for snap in _flatten_snapshots(snapshot_info["snapshots"]):
                    snap_age_hours = (datetime.now() - snap["creation_time"]).total_seconds() / 3600
                    if snap_age_hours > snapshot_limit_hours:
                        raise VSphereOperationError(
                            f"Snapshot {snap['name']} is older than {snapshot_limit_hours} hours. "
                            "Please delete old snapshots before creating new ones."
                        )
            
            # 创建快照
            task = vm.CreateSnapshot(
                name=snapshot_name,
                description=description,
                memory=memory,
                quiesce=quiesce
            )
            
            result = _wait_for_task(task)
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {
                "snapshot_name": snapshot_name,
                "snapshot_id": result.key,
            }
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to create snapshot: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise


@celery_app.task(bind=True, name="vm_tasks.revert_snapshot")
def revert_snapshot_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    snapshot_id: Optional[int] = None,
    snapshot_name: Optional[str] = None
) -> Dict[str, Any]:
    """回滚快照任务"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.snapshot.revert",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            # 找到目标快照
            snapshot = _find_snapshot(vm, snapshot_id, snapshot_name)
            if not snapshot:
                raise VSphereOperationError(
                    f"Snapshot not found: id={snapshot_id}, name={snapshot_name}"
                )
            
            # 回滚到快照
            task = snapshot.snapshot.RevertToSnapshotTask()
            result = _wait_for_task(task)
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {"reverted": True}
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to revert snapshot: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise


@celery_app.task(bind=True, name="vm_tasks.delete_snapshot")
def delete_snapshot_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    snapshot_id: Optional[int] = None,
    snapshot_name: Optional[str] = None,
    delete_children: bool = False
) -> Dict[str, Any]:
    """删除快照任务"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.snapshot.delete",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            # 找到目标快照
            snapshot = _find_snapshot(vm, snapshot_id, snapshot_name)
            if not snapshot:
                raise VSphereOperationError(
                    f"Snapshot not found: id={snapshot_id}, name={snapshot_name}"
                )
            
            # 删除快照
            task = snapshot.snapshot.RemoveTask(delete_children=delete_children)
            result = _wait_for_task(task)
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {"deleted": True}
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to delete snapshot: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise


@celery_app.task(bind=True, name="vm_tasks.vmotion")
def vmotion_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    target_host_name: Optional[str] = None,
    target_cluster_name: Optional[str] = None,
    priority: str = "default"  # default, high, low
) -> Dict[str, Any]:
    """vMotion 在线迁移任务"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.vmotion",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "target_host": target_host_name,
            "target_cluster": target_cluster_name,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            # 确定目标主机
            if target_host_name:
                target_host = client.get_host(target_host_name)
            elif target_cluster_name:
                cluster = client.get_cluster(target_cluster_name)
                if not cluster:
                    raise VSphereOperationError(f"Cluster {target_cluster_name} not found")
                # 选择负载最低的主机
                target_host = _select_least_loaded_host(client, cluster)
            else:
                raise ValueError("Must specify target_host or target_cluster")
            
            if not target_host:
                raise VSphereOperationError("No suitable target host found")
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 20, "step": "pre_migration_check"}
            )
            
            # 执行 vMotion 前检查
            _vmotion_pre_check(vm, target_host)
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 40, "step": "migration_started"}
            )
            
            # 确定优先级
            priority_flag = {
                "default": None,
                "high": vim.VirtualMachine.MovePriority.highPriority,
                "low": vim.VirtualMachine.MovePriority.lowPriority,
            }.get(priority)
            
            # 执行 vMotion
            task = vm.migrate(
                pool=target_host.parent.resourcePool,
                host=target_host,
                priority=priority_flag
            )
            
            result = _wait_for_task(task, timeout=1800)
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "step": "completed"}
            )
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {
                "migrated": True,
                "new_host": target_host.name,
            }
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to vMotion VM: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise


@celery_app.task(bind=True, name="vm_tasks.storage_vmotion")
def storage_vmotion_task(
    self,
    vcenter_id: str,
    vm_uuid: str,
    target_datastore_name: str
) -> Dict[str, Any]:
    """Storage vMotion 存储迁移任务"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="vm.storage_vmotion",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={
            "vm_uuid": vm_uuid,
            "target_datastore": target_datastore_name,
        }
    )
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vm = client.get_vm_by_uuid(vm_uuid)
            if not vm:
                raise VSphereOperationError(f"VM {vm_uuid} not found")
            
            target_datastore = client.get_datastore(target_datastore_name)
            if not target_datastore:
                raise VSphereOperationError(f"Datastore {target_datastore_name} not found")
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 20, "step": "pre_migration_check"}
            )
            
            # 执行 Storage vMotion
            task = vm.migrate(
                pool=None,  # 保持当前资源池
                host=None,   # 保持当前主机
                datastore=target_datastore,
                priority=vim.VirtualMachine.MovePriority.defaultPriority
            )
            
            result = _wait_for_task(task, timeout=3600)
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "step": "completed"}
            )
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = {
                "migrated": True,
                "new_datastore": target_datastore_name,
            }
            task_record.save()
            
            return task_record.result
            
    except Exception as e:
        logger.exception(f"Failed to Storage vMotion VM: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        raise
```

#### 3.2.3 数据同步任务

```python
# app/tasks/sync_tasks.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.tasks.celery_app import celery_app
from app.core.vsphere.client import VSphereClient

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="sync_tasks.full_sync")
def full_sync_task(
    self,
    vcenter_id: str,
    sync_datacenters: bool = True,
    sync_clusters: bool = True,
    sync_hosts: bool = True,
    sync_vms: bool = True,
    sync_storage: bool = True,
    sync_networks: bool = True
) -> Dict[str, Any]:
    """全量同步任务"""
    task_record = TaskRecord(
        task_id=self.request.id,
        task_type="sync.full",
        status=TaskStatus.RUNNING,
        start_time=datetime.now(),
        metadata={"vcenter_id": vcenter_id}
    )
    
    results = {
        "datacenters": 0,
        "clusters": 0,
        "hosts": 0,
        "vms": 0,
        "datastores": 0,
        "networks": 0,
        "errors": []
    }
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            total_steps = sum([
                sync_datacenters, sync_clusters, sync_hosts,
                sync_vms, sync_storage, sync_networks
            ])
            current_step = 0
            
            # 同步数据中心
            if sync_datacenters:
                current_step += 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(current_step / total_steps * 100),
                        "step": "syncing_datacenters"
                    }
                )
                datacenters = client.get_all_datacenters()
                for dc in datacenters:
                    _sync_datacenter(vcenter_id, dc)
                results["datacenters"] = len(datacenters)
            
            # 同步集群
            if sync_clusters:
                current_step += 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(current_step / total_steps * 100),
                        "step": "syncing_clusters"
                    }
                )
                clusters = client.get_all_clusters()
                for cluster in clusters:
                    _sync_cluster(vcenter_id, cluster)
                results["clusters"] = len(clusters)
            
            # 同步主机
            if sync_hosts:
                current_step += 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(current_step / total_steps * 100),
                        "step": "syncing_hosts"
                    }
                )
                hosts = client.get_all_hosts()
                for host in hosts:
                    _sync_host(vcenter_id, host)
                results["hosts"] = len(hosts)
            
            # 同步虚拟机
            if sync_vms:
                current_step += 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(current_step / total_steps * 100),
                        "step": "syncing_vms"
                    }
                )
                vms = client.get_all_vms()
                for vm in vms:
                    _sync_vm(vcenter_id, vm)
                results["vms"] = len(vms)
            
            # 同步存储
            if sync_storage:
                current_step += 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(current_step / total_steps * 100),
                        "step": "syncing_datastores"
                    }
                )
                datastores = client.get_all_datastores()
                for ds in datastores:
                    _sync_datastore(vcenter_id, ds)
                results["datastores"] = len(datastores)
            
            # 同步网络
            if sync_networks:
                current_step += 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(current_step / total_steps * 100),
                        "step": "syncing_networks"
                    }
                )
                networks = client.get_all_networks()
                for name, network in networks.items():
                    _sync_network(vcenter_id, network)
                results["networks"] = len(networks)
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "step": "completed"}
            )
            
            task_record.status = TaskStatus.SUCCESS
            task_record.end_time = datetime.now()
            task_record.result = results
            task_record.save()
            
            return results
            
    except Exception as e:
        logger.exception(f"Failed to perform full sync: {e}")
        
        task_record.status = TaskStatus.FAILED
        task_record.end_time = datetime.now()
        task_record.error = str(e)
        task_record.save()
        
        results["errors"].append(str(e))
        return results


@celery_app.task(bind=True, name="sync_tasks.incremental_sync")
def incremental_sync_task(
    self,
    vcenter_id: str
) -> Dict[str, Any]:
    """增量同步任务"""
    try:
        # 监听 vCenter 事件，获取变更
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            # 获取事件管理器
            event_manager = client.content.eventManager
            
            # 获取最近 N 分钟的事件
            since_time = datetime.now() - timedelta(minutes=5)
            
            # 构造过滤器
            filter_spec = vim.event.EventFilterSpec(
                time=vim.event.EventFilterSpec.byTime(
                    beginTime=since_time,
                    endTime=None
                ),
                eventTypeId=[
                    "VmCreatedEvent",
                    "VmClonedEvent",
                    "VmDeployedEvent",
                    "VmDestroyedEvent",
                    "VmPoweredOnEvent",
                    "VmPoweredOffEvent",
                    "VmReconfiguredEvent",
                    "VmMigratedEvent",
                    "VmSnapshotCreatedEvent",
                    "VmSnapshotRevertedEvent",
                    "VmSnapshotRemovedEvent",
                    "HostAddedEvent",
                    "HostRemovedEvent",
                    "ClusterCreatedEvent",
                    "ClusterDestroyedEvent",
                    "DatastoreAddedEvent",
                    "DatastoreRemovedEvent",
                ]
            )
            
            events = event_manager.QueryEvents(filter_spec)
            
            # 处理事件
            for event in events:
                _process_event(vcenter_id, event)
            
            return {"events_processed": len(events)}
            
    except Exception as e:
        logger.exception(f"Failed to perform incremental sync: {e}")
        raise


@celery_app.task(name="sync_tasks.scheduled_full_sync")
def scheduled_full_sync_task(vcenter_id: str):
    """定时全量同步任务"""
    # 根据配置的同步时间执行
    pass


@celery_app.task(name="sync_tasks.cleanup_expired_snapshots")
def cleanup_expired_snapshots_task(vcenter_id: str) -> Dict[str, Any]:
    """清理过期快照任务"""
    results = {"scanned": 0, "expired": 0, "deleted": 0, "errors": []}
    
    try:
        vcenter = get_vcenter_connection(vcenter_id)
        
        with VSphereClient(
            host=vcenter.host,
            user=vcenter.username,
            password=vcenter.password
        ) as client:
            vms = client.get_all_vms()
            
            for vm in vms:
                results["scanned"] += 1
                snapshot_info = client.get_vm_snapshot_info(vm)
                
                if not snapshot_info.get("has_snapshots"):
                    continue
                
                # 检查过期快照
                for snap in _flatten_snapshots(snapshot_info["snapshots"]):
                    snap_age_hours = (datetime.now() - snap["creation_time"]).total_seconds() / 3600
                    
                    if snap_age_hours > 72:  # 超过 72 小时
                        results["expired"] += 1
                        try:
                            # 删除过期快照
                            snap["snapshot"].RemoveTask()
                            results["deleted"] += 1
                        except Exception as e:
                            results["errors"].append({
                                "vm": vm.name,
                                "snapshot": snap["name"],
                                "error": str(e)
                            })
            
            return results
            
    except Exception as e:
        logger.exception(f"Failed to cleanup expired snapshots: {e}")
        raise
```

### 3.3 服务层设计

```python
# app/services/vm_service.py
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.tasks.celery_app import TaskResult
from app.tasks import vm_tasks
from app.repositories.vm_repository import VMRepository
from app.schemas.vm import (
    VMCreateRequest,
    VMUpdateRequest,
    VMResourceResizeRequest,
    SnapshotCreateRequest,
    VMPowerOperation
)

logger = logging.getLogger(__name__)


class VMService:
    """虚拟机服务"""
    
    def __init__(self):
        self.repository = VMRepository()
    
    async def create_vm(
        self,
        vcenter_id: str,
        datacenter_name: str,
        cluster_name: str,
        resource_pool_name: str,
        vm_config: VMCreateRequest
    ) -> TaskResult:
        """
        创建虚拟机
        
        Returns:
            TaskResult: 异步任务结果
        """
        # 验证配置
        self._validate_vm_config(vm_config)
        
        # 提交异步任务
        task = vm_tasks.create_vm_task.apply_async(
            args=[
                vcenter_id,
                datacenter_name,
                cluster_name,
                resource_pool_name,
                vm_config.model_dump()
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def power_operation(
        self,
        vcenter_id: str,
        vm_uuid: str,
        operation: VMPowerOperation
    ) -> TaskResult:
        """执行虚拟机电源操作"""
        task = vm_tasks.vm_power_operation_task.apply_async(
            args=[vcenter_id, vm_uuid, operation.value],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def resize_resources(
        self,
        vcenter_id: str,
        vm_uuid: str,
        resize_request: VMResourceResizeRequest
    ) -> TaskResult:
        """调整虚拟机资源"""
        task = vm_tasks.vm_resize_resources_task.apply_async(
            args=[
                vcenter_id,
                vm_uuid,
                resize_request.cpu,
                resize_request.memory_mb,
                resize_request.disk_size_gb
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def create_snapshot(
        self,
        vcenter_id: str,
        vm_uuid: str,
        snapshot_request: SnapshotCreateRequest
    ) -> TaskResult:
        """创建快照"""
        # 检查快照策略
        await self._check_snapshot_policy(vcenter_id, vm_uuid)
        
        task = vm_tasks.create_snapshot_task.apply_async(
            args=[
                vcenter_id,
                vm_uuid,
                snapshot_request.name,
                snapshot_request.description,
                snapshot_request.memory,
                snapshot_request.quiesce
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def delete_snapshot(
        self,
        vcenter_id: str,
        vm_uuid: str,
        snapshot_id: Optional[int] = None,
        snapshot_name: Optional[str] = None,
        delete_children: bool = False
    ) -> TaskResult:
        """删除快照"""
        task = vm_tasks.delete_snapshot_task.apply_async(
            args=[
                vcenter_id,
                vm_uuid,
                snapshot_id,
                snapshot_name,
                delete_children
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def revert_snapshot(
        self,
        vcenter_id: str,
        vm_uuid: str,
        snapshot_id: Optional[int] = None,
        snapshot_name: Optional[str] = None
    ) -> TaskResult:
        """回滚快照"""
        task = vm_tasks.revert_snapshot_task.apply_async(
            args=[
                vcenter_id,
                vm_uuid,
                snapshot_id,
                snapshot_name
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def vmotion(
        self,
        vcenter_id: str,
        vm_uuid: str,
        target_host_name: Optional[str] = None,
        target_cluster_name: Optional[str] = None,
        priority: str = "default"
    ) -> TaskResult:
        """vMotion 在线迁移"""
        task = vm_tasks.vmotion_task.apply_async(
            args=[
                vcenter_id,
                vm_uuid,
                target_host_name,
                target_cluster_name,
                priority
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def storage_vmotion(
        self,
        vcenter_id: str,
        vm_uuid: str,
        target_datastore_name: str
    ) -> TaskResult:
        """Storage vMotion 存储迁移"""
        task = vm_tasks.storage_vmotion_task.apply_async(
            args=[
                vcenter_id,
                vm_uuid,
                target_datastore_name
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def convert_to_template(
        self,
        vcenter_id: str,
        vm_uuid: str
    ) -> TaskResult:
        """将虚拟机转换为模板"""
        task = vm_tasks.convert_to_template_task.apply_async(
            args=[vcenter_id, vm_uuid],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    async def clone_from_template(
        self,
        vcenter_id: str,
        template_uuid: str,
        clone_request: VMCreateRequest
    ) -> TaskResult:
        """从模板克隆虚拟机"""
        task = vm_tasks.clone_from_template_task.apply_async(
            args=[
                vcenter_id,
                template_uuid,
                clone_request.model_dump()
            ],
            queue="vm_operations"
        )
        
        return TaskResult(task_id=task.id)
    
    def _validate_vm_config(self, config: VMCreateRequest):
        """验证虚拟机配置"""
        if config.cpu < 1 or config.cpu > 64:
            raise ValueError("CPU must be between 1 and 64")
        
        if config.memory_mb < 512 or config.memory_mb > 64 * 1024:
            raise ValueError("Memory must be between 512MB and 64TB")
        
        for disk in config.disks:
            if disk.size_gb < 1 or disk.size_gb > 64 * 1024:
                raise ValueError("Disk size must be between 1GB and 64TB")
    
    async def _check_snapshot_policy(self, vcenter_id: str, vm_uuid: str):
        """检查快照策略"""
        # 检查是否存在超过 72 小时的快照
        pass
```

---

## 4. API 接口设计

### 4.1 虚拟机 API

#### 4.1.1 创建虚拟机

```
POST /api/v1/vms
```

**Request Body:**
```json
{
  "vcenter_id": "vc-001",
  "datacenter_name": "DC1",
  "cluster_name": "Cluster1",
  "resource_pool_name": "RP1",
  "vm_config": {
    "name": "vm-web-001",
    "cpu": 4,
    "memory_mb": 8192,
    "guest_os": "ubuntu64Guest",
    "disks": [
      {
        "size_gb": 100,
        "thin_provisioned": true,
        "datastore_name": "NFS-Storage1"
      }
    ],
    "networks": [
      {
        "network_name": "VM Network",
        "adapter_type": "VMXNET3",
        "mac_address": "auto"
      }
    ]
  }
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "task-abc123",
  "status": "PENDING",
  "created_at": "2026-03-19T10:00:00Z"
}
```

#### 4.1.2 获取虚拟机详情

```
GET /api/v1/vms/{vm_uuid}
```

**Response (200 OK):**
```json
{
  "uuid": "vm-uuid-123",
  "name": "vm-web-001",
  "power_state": "poweredOn",
  "tools_status": "toolsOk",
  "tools_version": "12345",
  "ip_address": "192.168.1.100",
  "host_name": "esxi-01.example.com",
  "cpu": {
    "count": 4,
    "usage_percent": 25.5
  },
  "memory": {
    "size_mb": 8192,
    "usage_percent": 60.2
  },
  "disks": [
    {
      "label": "Hard disk 1",
      "capacity_gb": 100,
      "used_gb": 45.2,
      "datastore": "NFS-Storage1"
    }
  ],
  "networks": [
    {
      "label": "Network adapter 1",
      "network_name": "VM Network",
      "ip_address": "192.168.1.100",
      "mac_address": "00:50:56:a0:12:34"
    }
  ],
  "snapshots": {
    "has_snapshots": true,
    "count": 2,
    "snapshots": [
      {
        "id": 1,
        "name": "snap-before-update",
        "creation_time": "2026-03-19T09:00:00Z",
        "state": "poweredOn"
      }
    ]
  },
  "created_at": "2026-03-18T10:00:00Z",
  "updated_at": "2026-03-19T10:30:00Z"
}
```

#### 4.1.3 虚拟机电源操作

```
POST /api/v1/vms/{vm_uuid}/power
```

**Request Body:**
```json
{
  "operation": "start"  // start, stop, restart, suspend, resume
}
```

#### 4.1.4 调整虚拟机资源

```
PATCH /api/v1/vms/{vm_uuid}/resources
```

**Request Body:**
```json
{
  "cpu": 8,
  "memory_mb": 16384,
  "disk_size_gb": 200
}
```

#### 4.1.5 快照管理

```
POST /api/v1/vms/{vm_uuid}/snapshots
```

**Request Body:**
```json
{
  "name": "snap-before-maintenance",
  "description": "Snapshot before maintenance window",
  "memory": true,
  "quiesce": true
}
```

#### 4.1.6 vMotion 迁移

```
POST /api/v1/vms/{vm_uuid}/vmotion
```

**Request Body:**
```json
{
  "target_host_name": "esxi-02.example.com",
  "priority": "default"
}
```

### 4.2 主机 API

```
GET /api/v1/hosts
GET /api/v1/hosts/{host_uuid}
GET /api/v1/hosts/{host_uuid}/hardware
GET /api/v1/hosts/{host_uuid}/resources
```

### 4.3 集群 API

```
GET /api/v1/clusters
GET /api/v1/clusters/{cluster_uuid}
GET /api/v1/clusters/{cluster_uuid}/resources
GET /api/v1/clusters/{cluster_uuid}/ha
GET /api/v1/clusters/{cluster_uuid}/drs
```

### 4.4 存储 API

```
GET /api/v1/datastores
GET /api/v1/datastores/{datastore_uuid}
POST /api/v1/datastores/{datastore_uuid}/resize
```

### 4.5 网络 API

```
GET /api/v1/networks
GET /api/v1/networks/{network_uuid}
POST /api/v1/networks
DELETE /api/v1/networks/{network_uuid}
```

### 4.6 任务 API

```
GET /api/v1/tasks/{task_id}
GET /api/v1/tasks/{task_id}/cancel
GET /api/v1/tasks
```

---

## 5. 数据模型设计

### 5.1 数据库模型

#### 5.1.1 任务记录表

```sql
CREATE TABLE task_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL UNIQUE,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    priority VARCHAR(10) DEFAULT 'P2-Normal',
    vcenter_id VARCHAR(50),
    target_object_type VARCHAR(50),
    target_object_id VARCHAR(100),
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(100),
    result JSONB,
    error TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_status CHECK (status IN (
        'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED'
    ))
);

CREATE INDEX idx_task_records_status ON task_records(status);
CREATE INDEX idx_task_records_vcenter ON task_records(vcenter_id);
CREATE INDEX idx_task_records_created ON task_records(created_at);
```

#### 5.1.2 虚拟机表

```sql
CREATE TABLE vms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vcenter_id VARCHAR(50) NOT NULL,
    vm_uuid VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    power_state VARCHAR(20),
    tools_status VARCHAR(20),
    tools_version VARCHAR(20),
    ip_address VARCHAR(45),
    host_uuid VARCHAR(100),
    cluster_uuid VARCHAR(100),
    datacenter_uuid VARCHAR(100),
    resource_pool_uuid VARCHAR(100),
    cpu_count INTEGER,
    memory_mb INTEGER,
    disk_capacity_bytes BIGINT,
    guest_os VARCHAR(100),
    is_template BOOLEAN DEFAULT FALSE,
    snapshot_count INTEGER DEFAULT 0,
    last_sync_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_power_state CHECK (power_state IN (
        'poweredOn', 'poweredOff', 'suspended', 'unknown'
    ))
);

CREATE INDEX idx_vms_vcenter ON vms(vcenter_id);
CREATE INDEX idx_vms_host ON vms(host_uuid);
CREATE INDEX idx_vms_cluster ON vms(cluster_uuid);
CREATE INDEX idx_vms_ip ON vms(ip_address);
```

#### 5.1.3 快照表

```sql
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vcenter_id VARCHAR(50) NOT NULL,
    vm_uuid VARCHAR(100) NOT NULL,
    snapshot_uuid VARCHAR(100),
    snapshot_id INTEGER,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    state VARCHAR(20),
    memory_dump BOOLEAN,
    quiesce BOOLEAN,
    creation_time TIMESTAMP WITH TIME ZONE NOT NULL,
    parent_snapshot_id INTEGER,
    is_expired BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_vm FOREIGN KEY (vm_uuid) REFERENCES vms(vm_uuid) ON DELETE CASCADE
);

CREATE INDEX idx_snapshots_vm ON snapshots(vm_uuid);
CREATE INDEX idx_snapshots_expired ON snapshots(is_expired);
```

#### 5.1.4 操作审计日志表

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vcenter_id VARCHAR(50),
    operator_id VARCHAR(100),
    operator_name VARCHAR(255),
    operation_type VARCHAR(50) NOT NULL,
    target_object_type VARCHAR(50),
    target_object_id VARCHAR(100),
    target_object_name VARCHAR(255),
    operation_detail JSONB,
    before_state JSONB,
    after_state JSONB,
    result VARCHAR(20),
    error_message TEXT,
    request_id VARCHAR(100),
    request_ip VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_vcenter ON audit_logs(vcenter_id);
CREATE INDEX idx_audit_operator ON audit_logs(operator_id);
CREATE INDEX idx_audit_target ON audit_logs(target_object_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
```

### 5.2 Pydantic 模型

```python
# app/schemas/vm.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class VMPowerState(str, Enum):
    POWERED_ON = "poweredOn"
    POWERED_OFF = "poweredOff"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class VMToolsStatus(str, Enum):
    TOOLS_OK = "toolsOk"
    TOOLS_NOT_INSTALLED = "toolsNotInstalled"
    TOOLS_OUT_OF_DATE = "toolsOld"
    TOOLS_RUNNING = "toolsRunning"
    TOOLS_NOT_RUNNING = "toolsNotRunning"


class VMPowerOperation(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    SUSPEND = "suspend"
    RESUME = "resume"


class DiskConfig(BaseModel):
    size_gb: int = Field(..., ge=1, le=64*1024)
    thin_provisioned: bool = True
    datastore_name: Optional[str] = None
    disk_type: str = "thin"


class NetworkConfig(BaseModel):
    network_name: str
    adapter_type: str = "VMXNET3"
    mac_address: str = "auto"
    vlan_id: Optional[int] = None


class VMCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    cpu: int = Field(..., ge=1, le=64)
    memory_mb: int = Field(..., ge=512, le=64*1024)
    guest_os: str
    disks: List[DiskConfig] = Field(default_factory=list)
    networks: List[NetworkConfig] = Field(default_factory=list)
    annotation: Optional[str] = None


class VMUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    annotation: Optional[str] = None


class VMResourceResizeRequest(BaseModel):
    cpu: Optional[int] = Field(None, ge=1, le=64)
    memory_mb: Optional[int] = Field(None, ge=512, le=64*1024)
    disk_size_gb: Optional[int] = Field(None, ge=1, le=64*1024)


class DiskInfo(BaseModel):
    label: str
    capacity_gb: float
    used_gb: float
    datastore: str
    thin_provisioned: bool


class NetworkInfo(BaseModel):
    label: str
    network_name: str
    ip_address: Optional[str]
    mac_address: str
    connected: bool


class SnapshotInfo(BaseModel):
    id: int
    name: str
    description: Optional[str]
    creation_time: datetime
    state: str
    children: List["SnapshotInfo"] = []


class SnapshotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    memory: bool = False
    quiesce: bool = False


class VMResponse(BaseModel):
    uuid: str
    name: str
    power_state: VMPowerState
    tools_status: VMToolsStatus
    tools_version: Optional[str]
    ip_address: Optional[str]
    host_name: Optional[str]
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disks: List[DiskInfo]
    networks: List[NetworkInfo]
    snapshots: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

## 6. 错误处理与回滚机制

### 6.1 异常类定义

```python
# app/core/vsphere/exceptions.py
from typing import Optional, Any, Dict


class VSphereException(Exception):
    """vSphere 相关异常基类"""
    
    def __init__(
        self,
        message: str,
        code: str = "VSPHERE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class VSphereConnectionError(VSphereException):
    """连接 vCenter 失败"""
    
    def __init__(self, message: str, host: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="CONNECTION_ERROR",
            details={"host": host, **(details or {})}
        )


class VSphereObjectNotFoundError(VSphereException):
    """vSphere 对象未找到"""
    
    def __init__(
        self,
        obj_type: str,
        obj_name: str,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=f"{obj_type} '{obj_name}' not found",
            code="OBJECT_NOT_FOUND",
            details={"object_type": obj_type, "object_name": obj_name, **(details or {})}
        )


class VSphereOperationError(VSphereException):
    """vSphere 操作失败"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        task_error: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=message,
            code="OPERATION_ERROR",
            details={
                "operation": operation,
                "task_error": task_error,
                **(details or {})
            }
        )


class VSphereTaskTimeoutError(VSphereException):
    """vSphere 任务超时"""
    
    def __init__(self, task_id: str, timeout: int, details: Optional[Dict] = None):
        super().__init__(
            message=f"Task {task_id} timed out after {timeout} seconds",
            code="TASK_TIMEOUT",
            details={"task_id": task_id, "timeout": timeout, **(details or {})}
        )


class VSphereResourceInsufficientError(VSphereException):
    """资源不足"""
    
    def __init__(
        self,
        resource_type: str,
        required: Any,
        available: Any,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=f"Insufficient {resource_type}: required {required}, available {available}",
            code="RESOURCE_INSUFFICIENT",
            details={
                "resource_type": resource_type,
                "required": required,
                "available": available,
                **(details or {})
            }
        )


class VSphereRollbackError(VSphereException):
    """回滚失败"""
    
    def __init__(self, original_error: str, rollback_error: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"Rollback failed: {rollback_error}",
            code="ROLLBACK_ERROR",
            details={
                "original_error": original_error,
                "rollback_error": rollback_error,
                **(details or {})
            }
        )


class TaskCancelledError(VSphereException):
    """任务被取消"""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task {task_id} was cancelled",
            code="TASK_CANCELLED",
            details={"task_id": task_id}
        )
```

### 6.2 回滚机制

```python
# 回滚装饰器
from functools import wraps
from typing import Callable, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self):
        self._rollback_actions: List[Tuple[Callable, tuple, dict]] = []
    
    def register(self, action: Callable, *args, **kwargs):
        """注册回滚操作"""
        self._rollback_actions.append((action, args, kwargs))
    
    def execute(self):
        """执行所有回滚操作"""
        errors = []
        for action, args, kwargs in reversed(self._rollback_actions):
            try:
                action(*args, **kwargs)
                logger.info(f"Rollback action {action.__name__} succeeded")
            except Exception as e:
                logger.error(f"Rollback action {action.__name__} failed: {e}")
                errors.append({
                    "action": action.__name__,
                    "error": str(e)
                })
        
        if errors:
            raise VSphereRollbackError(
                original_error="Multiple rollback errors",
                rollback_error=str(errors)
            )
    
    def clear(self):
        """清空回滚队列"""
        self._rollback_actions.clear()


def with_rollback(operation_name: str):
    """带回滚的装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rollback_manager = RollbackManager()
            
            try:
                result = func(*args, rollback_manager=rollback_manager, **kwargs)
                rollback_manager.clear()
                return result
            except Exception as e:
                logger.error(f"Operation {operation_name} failed, executing rollback")
                try:
                    rollback_manager.execute()
                except VSphereRollbackError as re:
                    logger.error(f"Rollback itself failed: {re}")
                    raise VSphereRollbackError(
                        original_error=str(e),
                        rollback_error=str(re)
                    )
                raise
        
        return wrapper
    return decorator


# 使用示例
@with_rollback(operation_name="create_vm")
def create_vm_with_rollback(
    vm_config: Dict[str, Any],
    rollback_manager: RollbackManager
) -> Dict[str, Any]:
    """创建虚拟机（带回滚）"""
    
    # 1. 创建磁盘
    disk = create_disk(vm_config["datastore"], vm_config["disk_size"])
    rollback_manager.register(delete_disk, disk.id)
    
    # 2. 创建网络
    network = create_network(vm_config["network_name"])
    rollback_manager.register(delete_network, network.id)
    
    # 3. 创建虚拟机
    vm = create_vm(vm_config)
    rollback_manager.register(destroy_vm, vm.uuid)
    
    # 4. 挂载磁盘
    attach_disk(vm.id, disk.id)
    rollback_manager.register(detach_disk, disk.id)
    
    # 5. 连接网络
    connect_network(vm.id, network.id)
    rollback_manager.register(disconnect_network, network.id)
    
    return vm
```

### 6.3 任务重试与超时

```python
# 任务重试配置
@celery_app.task(
    bind=True,
    name="vm_tasks.create_vm",
    autoretry_for=(
        VSphereConnectionError,
        VSphereOperationError,
        VSphereTaskTimeoutError,
    ),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def create_vm_task(self, ...):
    """创建虚拟机任务（带自动重试）"""
    try:
        # 业务逻辑
        ...
    except VSphereConnectionError as e:
        # 连接错误，指数退避重试
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
    except VSphereTaskTimeoutError as e:
        # 超时错误，增加超时时间重试
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
```

---

## 7. 异步任务流程图

### 7.1 虚拟机创建流程

```
用户请求创建VM
       │
       ▼
┌─────────────────┐
│  验证请求参数   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  提交异步任务   │
│  (TaskQueue)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  连接 vCenter   │
│  (ConnectionPool│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  获取目标位置   │
│  (Datacenter,   │
│   Cluster, RP)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  构建 VM 配置   │
│  (VmCreateSpec)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  调用 vSphere   │
│  CreateVM API   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  等待任务完成   │
│  (WaitForTask)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ 成功？   │
    └────┬────┘
    Yes  │  No
    ┌────┴──────────────────────┐
    ▼                           ▼
┌─────────┐              ┌─────────────────┐
│ 更新进度 │              │  执行回滚操作    │
│ 100%    │              │  (RollbackMgr)  │
└────┬────┘              └────────┬────────┘
     │                            │
     ▼                            ▼
┌─────────────────┐        ┌─────────────────┐
│  记录任务结果   │        │  记录错误信息    │
│  (SUCCESS)      │        │  (FAILED)        │
└─────────────────┘        └─────────────────┘
```

### 7.2 vMotion 迁移流程

```
用户请求 vMotion
       │
       ▼
┌─────────────────┐
│  验证 VM 状态   │
│  (必须是运行中) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  确定目标主机   │
│  (指定或选择    │
│   负载最低)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CPU 兼容性检查 │
│  (EVC 模式)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  内存资源检查   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  网络连通性检查 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  提交迁移任务   │
│  (MigrateVM_Task│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  分阶段执行     │
│  1. 准备阶段    │
│  2. 迁移阶段    │
│  3. 切换阶段    │
└────────┬────────┘
         │
    ┌────┴────┐
    │ 成功？   │
    └────┬────┘
    Yes  │  No
    ┌────┴──────────────────────┐
    ▼                           ▼
┌─────────┐              ┌─────────────────┐
│ 更新状态 │              │  记录错误信息    │
│ (SUCCESS)│              │  (FAILED)        │
└─────────┘              └─────────────────┘
```

---

## 8. 配置管理

### 8.1 配置文件结构

```yaml
# config.yaml
app:
  name: "vmware-cloud-manager"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 8080

database:
  host: "postgres"
  port: 5432
  username: "vmware_cm"
  password: "${DB_PASSWORD}"
  name: "vmware_cm"
  pool_size: 20
  max_overflow: 10

redis:
  host: "redis"
  port: 6379
  password: "${REDIS_PASSWORD}"
  db: 0
  max_connections: 100

vcenter:
  connection_pool_size: 10
  connection_timeout: 30
  idle_timeout: 300
  retry_max_attempts: 3
  retry_backoff_base: 2

celery:
  broker_url: "redis://redis:6379/0"
  result_backend: "redis://redis:6379/1"
  task_serializer: "json"
  result_serializer: "json"
  timezone: "UTC"
  task_track_started: true
  task_time_limit: 3600
  task_soft_time_limit: 3300

sync:
  full_sync_interval: 86400  # 24 hours in seconds
  incremental_sync_interval: 300  # 5 minutes in seconds
  batch_size: 100
  snapshot_expiration_hours: 72

logging:
  level: "INFO"
  format: "json"
  output: "stdout"

snapshot_policy:
  max_age_hours: 72
  warning_hours_before: 24
  auto_cleanup_enabled: true
  auto_cleanup_time: "03:00"
```

### 8.2 环境变量

```bash
# 必需的环境变量
export VSPHERE_HOST="vcenter.example.com"
export VSPHERE_USERNAME="admin@vsphere.local"
export VSPHERE_PASSWORD="secret"

# 数据库
export DB_PASSWORD="postgres_password"

# Redis
export REDIS_PASSWORD="redis_password"

# 可选
export LOG_LEVEL="DEBUG"
export SYNC_INTERVAL="3600"
```

---

## 9. 安全设计

### 9.1 认证与授权

```python
# app/core/security.py
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RBAC:
    """基于角色的访问控制"""
    
    ROLES = {
        "admin": [
            "vm:*",
            "host:*",
            "cluster:*",
            "datastore:*",
            "network:*",
            "task:*",
            "vcenter:*",
        ],
        "operator": [
            "vm:read",
            "vm:create",
            "vm:power:*",
            "vm:snapshot:*",
            "vm:vmotion",
            "host:read",
            "cluster:read",
            "datastore:read",
            "network:read",
            "task:*",
        ],
        "viewer": [
            "vm:read",
            "host:read",
            "cluster:read",
            "datastore:read",
            "network:read",
            "task:read",
        ]
    }
    
    @classmethod
    def check_permission(cls, role: str, permission: str) -> bool:
        """检查权限"""
        if role not in cls.ROLES:
            return False
        
        role_permissions = cls.ROLES[role]
        
        for rp in role_permissions:
            if rp == "*":
                return True
            if rp == permission:
                return True
            if rp.endswith(":*") and permission.startswith(rp[:-1]):
                return True
        
        return False
```

### 9.2 审计日志

```python
# app/middleware/audit.py
from typing import Optional
from datetime import datetime
import json
import structlog

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        # 记录请求
        response = await call_next(request)
        
        # 构造审计日志
        audit_data = {
            "timestamp": start_time.isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "user_id": getattr(request.state, "user_id", None),
            "response_status": response.status_code,
            "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
        }
        
        # 如果是写操作，记录操作详情
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            try:
                body = await request.body()
                if body:
                    audit_data["request_body"] = json.loads(body)
            except Exception:
                pass
            
            logger.info(
                "audit_log",
                **audit_data
            )
        
        return response
```

---

## 10. 监控与告警

### 10.1 健康检查

```python
# app/api/routes/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.vsphere.pool import VSphereConnectionPool

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """详细健康检查"""
    checks = {
        "database": await check_database(db),
        "redis": await check_redis(),
        "vcenter_pool": check_vcenter_pool(),
        "celery_workers": await check_celery_workers(),
    }
    
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


async def check_database(db: Session) -> dict:
    """检查数据库连接"""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_redis() -> dict:
    """检查 Redis 连接"""
    try:
        from app.core.redis import redis_client
        redis_client.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def check_vcenter_pool() -> dict:
    """检查 vCenter 连接池"""
    try:
        from app.core.vsphere import connection_pool
        stats = connection_pool.get_stats()
        return {
            "status": "healthy",
            "pools": stats
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_celery_workers() -> dict:
    """检查 Celery Workers"""
    try:
        from app.tasks.celery_app import celery_app
        
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        
        if not stats:
            return {"status": "unhealthy", "error": "No workers available"}
        
        return {
            "status": "healthy",
            "workers": len(stats),
            "worker_details": stats
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 10.2 指标暴露

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
import time

# 请求指标
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# vSphere 连接指标
vcenter_connections_active = Gauge(
    "vcenter_connections_active",
    "Number of active vCenter connections",
    ["vcenter_host"]
)

vcenter_connection_errors = Counter(
    "vcenter_connection_errors_total",
    "Total vCenter connection errors",
    ["vcenter_host", "error_type"]
)

# 任务指标
tasks_total = Counter(
    "tasks_total",
    "Total number of tasks",
    ["task_type", "status"]
)

task_duration_seconds = Histogram(
    "task_duration_seconds",
    "Task duration in seconds",
    ["task_type"]
)

tasks_in_progress = Gauge(
    "tasks_in_progress",
    "Number of tasks currently in progress",
    ["task_type"]
)

# 资源指标
vms_total = Gauge(
    "vms_total",
    "Total number of VMs",
    ["vcenter_id", "power_state"]
)

hosts_total = Gauge(
    "hosts_total",
    "Total number of ESXi hosts",
    ["vcenter_id"]
)

datastores_total = Gauge(
    "datastores_total",
    "Total number of datastores",
    ["vcenter_id"]
)

# 快照指标
snapshots_total = Gauge(
    "snapshots_total",
    "Total number of snapshots",
    ["vcenter_id"]
)

expired_snapshots_total = Gauge(
    "expired_snapshots_total",
    "Number of expired snapshots",
    ["vcenter_id"]
)
```

---

## 11. 附录

### 11.1 vSphere API 兼容性矩阵

| 功能 | vSphere 6.7 | vSphere 7.0 | vSphere 8.0 |
|------|-------------|-------------|-------------|
| 基本 VM 操作 | ✓ | ✓ | ✓ |
| 热添加 CPU/内存 | ✓ | ✓ | ✓ |
| vMotion | ✓ | ✓ | ✓ |
| Storage vMotion | ✓ | ✓ | ✓ |
| 分布式交换机 | ✓ | ✓ | ✓ |
| vSAN | ✓ | ✓ | ✓ |
| HA/DRS | ✓ | ✓ | ✓ |
| 快照热添加 | ✓ | ✓ | ✓ |
| 虚拟机模板 | ✓ | ✓ | ✓ |
| 资源池 | ✓ | ✓ | ✓ |

### 11.2 pyVmomi 版本兼容性

| pyVmomi 版本 | 支持的 vSphere 版本 |
|--------------|-------------------|
| 7.0.x | vSphere 6.7, 7.0 |
| 8.0.x | vSphere 7.0, 8.0 |
| 8.1.x | vSphere 8.0+ |

### 11.3 错误代码映射

| 错误代码 | 说明 | HTTP 状态码 |
|----------|------|-------------|
| VSPHERE_ERROR | 通用 vSphere 错误 | 500 |
| CONNECTION_ERROR | 连接错误 | 503 |
| OBJECT_NOT_FOUND | 对象未找到 | 404 |
| OPERATION_ERROR | 操作失败 | 400 |
| TASK_TIMEOUT | 任务超时 | 504 |
| RESOURCE_INSUFFICIENT | 资源不足 | 507 |
| ROLLBACK_ERROR | 回滚失败 | 500 |
| TASK_CANCELLED | 任务取消 | 499 |
| PERMISSION_DENIED | 权限不足 | 403 |
| VALIDATION_ERROR | 参数验证失败 | 422 |

### 11.4 术语表

| 术语 | 说明 |
|------|------|
| MoRef | Managed Object Reference，vSphere 对象的唯一标识符 |
| EVC | Enhanced vMotion Compatibility，增强型 vMotion 兼容性模式 |
| SIOC | Storage I/O Control，存储 I/O 控制 |
| sVMotion | Storage vMotion，存储 vMotion |
| DRS | Distributed Resource Scheduler，分布式资源调度 |
| SDRS | Storage DRS，存储分布式资源调度 |
| CBT | Changed Block Tracking，变更块追踪 |
| FT | Fault Tolerance，容错 |
