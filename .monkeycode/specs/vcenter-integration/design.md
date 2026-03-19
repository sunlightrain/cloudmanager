# VMware vCenter 集成技术设计文档

## 1. 架构设计

### 1.1 模块结构

```
backend/app/
├── core/
│   └── vsphere.py          # vCenter 连接管理（单例）
├── services/
│   ├── inventory_service.py     # inventory 同步服务
│   ├── vm_service.py             # 虚拟机生命周期服务
│   ├── snapshot_service.py       # 快照管理服务
│   ├── storage_service.py        # 存储管理服务
│   ├── network_service.py        # 网络管理服务
│   └── task_service.py           # 异步任务服务
├── api/routes/
│   ├── inventory.py        # 数据中心/集群/主机 API
│   ├── vms.py              # 虚拟机 API
│   ├── snapshots.py        # 快照 API
│   ├── storage.py          # 存储 API
│   └── network.py          # 网络 API
└── models/
    ├── datacenter.py       # 数据中心模型
    ├── cluster.py          # 集群模型
    ├── host.py             # 主机模型
    ├── vm.py               # 虚拟机模型
    ├── storage.py          # 存储模型
    └── network.py          # 网络模型
```

### 1.2 核心组件

#### vSphere Client（单例模式）

```python
# backend/app/core/vsphere.py
from pyvim.connect import SmartConnect, Disconnect
from threading import Lock

class VsphereClient:
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        self._client = None
        self._host = None
    
    @classmethod
    def get_instance(cls) -> "VsphereClient":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def connect(self, host: str, port: int, username: str, password: str):
        self._client = SmartConnect(
            host=host,
            port=port,
            user=username,
            pwd=password
        )
        self._host = host
    
    def get_client(self):
        return self._client
    
    def disconnect(self):
        if self._client:
            Disconnect(self._client)
```

#### 异步任务执行器

```python
# backend/app/services/task_service.py
import asyncio
from enum import Enum
from typing import Callable, Any
from uuid import uuid4

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskExecutor:
    def __init__(self):
        self._tasks = {}
    
    async def execute(self, name: str, func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid4())
        self._tasks[task_id] = {
            "id": task_id,
            "name": name,
            "status": TaskStatus.PENDING,
            "result": None,
            "error": None
        }
        
        asyncio.create_task(self._run(task_id, func, *args, **kwargs))
        return task_id
    
    async def _run(self, task_id: str, func: Callable, *args, **kwargs):
        try:
            self._tasks[task_id]["status"] = TaskStatus.RUNNING
            result = await func(*args, **kwargs)
            self._tasks[task_id]["status"] = TaskStatus.COMPLETED
            self._tasks[task_id]["result"] = result
        except Exception as e:
            self._tasks[task_id]["status"] = TaskStatus.FAILED
            self._tasks[task_id]["error"] = str(e)
    
    def get_task(self, task_id: str) -> dict:
        return self._tasks.get(task_id)
```

## 2. API 设计

### 2.1 清单管理 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/inventory/datacenters` | 获取数据中心列表 |
| GET | `/api/inventory/clusters` | 获取集群列表 |
| GET | `/api/inventory/clusters/{id}` | 获取集群详情 |
| GET | `/api/inventory/hosts` | 获取主机列表 |
| GET | `/api/inventory/hosts/{id}` | 获取主机详情 |
| POST | `/api/inventory/sync` | 触发全量同步 |

### 2.2 虚拟机 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/vms` | 获取虚拟机列表 |
| GET | `/api/vms/{id}` | 获取虚拟机详情 |
| POST | `/api/vms` | 创建虚拟机 |
| PUT | `/api/vms/{id}` | 更新虚拟机配置 |
| DELETE | `/api/vms/{id}` | 删除虚拟机 |
| POST | `/api/vms/{id}/power-on` | 开机 |
| POST | `/api/vms/{id}/power-off` | 关机 |
| POST | `/api/vms/{id}/restart` | 重启 |
| POST | `/api/vms/{id}/suspend` | 挂起 |
| POST | `/api/vms/{id}/resume` | 恢复 |
| POST | `/api/vms/{id}/reconfigure` | 重新配置（CPU/内存/磁盘） |
| POST | `/api/vms/{id}/migrate` | 迁移（vMotion） |
| POST | `/api/vms/batch` | 批量创建 |

### 2.3 快照 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/vms/{id}/snapshots` | 获取快照列表 |
| POST | `/api/vms/{id}/snapshots` | 创建快照 |
| POST | `/api/vms/{id}/snapshots/{sid}/revert` | 回滚到快照 |
| DELETE | `/api/vms/{id}/snapshots/{sid}` | 删除快照 |
| POST | `/api/vms/{id}/snapshots/cleanup` | 清理所有快照 |

### 2.4 存储 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/storage/datastores` | 获取存储列表 |
| GET | `/api/storage/datastores/{id}` | 获取存储详情 |
| POST | `/api/storage/disks` | 挂载磁盘 |
| DELETE | `/api/storage/disks/{id}` | 卸载磁盘 |

### 2.5 网络 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/network/switches` | 获取交换机列表 |
| GET | `/api/network/portgroups` | 获取端口组列表 |
| POST | `/api/network/portgroups` | 创建端口组 |
| DELETE | `/api/network/portgroups/{id}` | 删除端口组 |
| POST | `/api/vms/{id}/nics` | 添加网卡 |
| DELETE | `/api/vms/{id}/nics/{nic_id}` | 移除网卡 |

## 3. 数据模型

### 3.1 vCenter 同步数据模型

```python
# backend/app/models/datacenter.py
from sqlmodel import SQLModel, Field
from typing import Optional

class Datacenter(SQLModel, table=True):
    __tablename__ = "datacenters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    name: str
    raw_data: str  # JSON
    last_sync: datetime
```

### 3.2 虚拟机缓存模型

```python
# backend/app/models/vm.py
from sqlmodel import SQLModel, Field
from typing import Optional, List

class VM(SQLModel, table=True):
    __tablename__ = "vms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vm_id: str = Field(unique=True, index=True)  # vCenter 中的 VM UUID
    name: str
    status: str  # poweredOn, poweredOff, suspended
    cpu: int
    memory_mb: int
    disk_gb: List[int]  # JSON
    ip_addresses: List[str]  # JSON
    tools_status: str
    guest_state: str
    host_id: Optional[int] = Field(foreign_key="hosts.id")
    datacenter_id: Optional[int] = Field(foreign_key="datacenters.id")
    last_sync: datetime
```

## 4. 关键实现

### 4.1 异步 VM 创建

```python
# backend/app/services/vm_service.py
class VMService:
    async def create_vm(self, config: VMCreate) -> str:
        task_id = await self.task_executor.execute(
            "create_vm",
            self._create_vm_task,
            config
        )
        return task_id
    
    async def _create_vm_task(self, config: VMCreate):
        client = VsphereClient.get_instance().get_client()
        content = client.content
        
        # 获取目标位置
        datacenter = self._find_datacenter(content, config.datacenter_id)
        vm_folder = datacenter.vmFolder
        
        # 创建虚拟机规格
        resource_pool = self._get_resource_pool(config.cluster_id)
        
        # 创建 VM
        task = vm_folder.CreateVM(
            config=self._build_vm_config_spec(config),
            pool=resource_pool,
            host=None
        )
        
        # 等待完成
        self._wait_for_task(task)
        
        return {"vm_id": task.info.result.config.uuid}
```

### 4.2 在线资源变更（Hot-add）

```python
    async def hot_resize(self, vm_id: str, cpu: int = None, memory_mb: int = None):
        vm = self._get_vm_by_id(vm_id)
        spec = VimVmReloadSpec()
        
        if cpu:
            spec.numCPUs = cpu
        if memory_mb:
            spec.memoryMB = memory_mb
        
        task = vm.Reconfigure(spec)
        self._wait_for_task(task)
```

### 4.3 vMotion 迁移

```python
    async def migrate_vm(self, vm_id: str, target_host_id: int, target_datastore_id: int = None):
        vm = self._get_vm_by_id(vm_id)
        target_host = self._get_host_by_id(target_host_id)
        
        relocate_spec = VimVmRelocateSpec()
        relocate_spec.host = target_host
        relocate_spec.pool = target_host.parent.resourcePool
        
        if target_datastore_id:
            relocate_spec.datastore = self._get_datastore_by_id(target_datastore_id)
        
        task = vm.RelocateVM(spec=relocate_spec, priority=VimVirtualMachineMovePriority.default)
        self._wait_for_task(task)
```

## 5. 错误处理与重试

```python
# backend/app/core/vsphere.py
class VsphereConnectionError(Exception):
    pass

class VsphereOperationError(Exception):
    pass

def with_retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
            raise VsphereOperationError(f"Failed after {max_attempts} attempts: {last_error}")
        return wrapper
    return decorator
```

## 6. 实施计划

| 阶段 | 任务 | 预估工时 |
|------|------|----------|
| 1 | 基础设施：vsphere client 单例、连接管理 | 1 天 |
| 2 | 清单同步：数据中心/集群/主机/存储/网络 | 2 天 |
| 3 | VM 生命周期：CRUD + 电源操作 | 2 天 |
| 4 | VM 高级操作：热添加、迁移、快照 | 2 天 |
| 5 | 存储管理：磁盘挂载/卸载、存储迁移 | 1 天 |
| 6 | 网络管理：端口组、网卡管理 | 1 天 |
| 7 | HA/DRS 集成 | 1 天 |
| 8 | 测试与调优 | 2 天 |

**总计**：约 12 个工作日
