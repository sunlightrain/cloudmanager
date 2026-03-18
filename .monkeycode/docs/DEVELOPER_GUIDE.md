# 开发指南

## 环境准备

### 系统要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (可选)

### 后端开发环境

1. 创建虚拟环境:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

2. 安装依赖:

```bash
pip install -r requirements.txt
```

3. 配置环境变量:

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要参数
```

4. 初始化数据库:

```bash
python -c "from app.core.database import init_db; init_db()"
```

5. 启动开发服务器:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发环境

1. 安装依赖:

```bash
cd frontend
npm install
```

2. 启动开发服务器:

```bash
npm run dev
```

## 项目结构说明

### 后端结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── api/                 # API路由
│   │   ├── __init__.py
│   │   ├── deps.py          # 依赖注入
│   │   ├── routes/
│   │   │   ├── auth.py      # 认证接口
│   │   │   ├── vms.py      # 虚拟机接口
│   │   │   ├── tasks.py    # 任务接口
│   │   │   ├── hosts.py    # 主机接口
│   │   │   └── settings.py # 系统设置
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── security.py      # 安全工具
│   │   └── vsphere.py       # vSphere客户端
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── task.py
│   │   └── operation_log.py
│   ├── schemas/             # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── vm.py
│   │   ├── task.py
│   │   └── common.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── vm_service.py
│   │   ├── task_service.py
│   │   └── vsphere_client.py
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── logger.py
├── requirements.txt
├── .env.example
└── tests/
```

### 前端结构

```
frontend/
├── src/
│   ├── api/                 # API调用
│   │   ├── index.ts
│   │   ├── auth.ts
│   │   ├── vms.ts
│   │   └── tasks.ts
│   ├── components/          # 公共组件
│   │   ├── VmStatus.vue
│   │   └── TaskStatus.vue
│   ├── layouts/             # 布局
│   │   └── Default.vue
│   ├── router/              # 路由配置
│   │   └── index.ts
│   ├── stores/              # Pinia状态管理
│   │   ├── auth.ts
│   │   └── vms.ts
│   ├── views/               # 页面
│   │   ├── Login.vue
│   │   ├── Dashboard.vue
│   │   ├── VmList.vue
│   │   ├── VmDetail.vue
│   │   ├── VmCreate.vue
│   │   ├── Snapshots.vue
│   │   ├── Tasks.vue
│   │   └── Settings.vue
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 核心功能开发

### 1. vSphere连接

使用pyvmomi连接vCenter:

```python
from pyvim.connect import SmartConnect, Disconnect
from app.core.vsphere import get_vsphere_client

# 获取vSphere客户端
client = await get_vsphere_client()

# 获取所有虚拟机
content = client.content
vm_folder = content.rootFolder.childEntity[0].vmFolder
vms = vm_folder.childEntity
```

### 2. 创建虚拟机

```python
from app.services.vm_service import VMService
from app.schemas.vm import VMCreate

vm_service = VMService()
vm_data = VMCreate(
    name="new-vm",
    cpu=2,
    memory_mb=4096,
    disk_gb=50,
    network_name="VM Network",
    datastore="datastore1",
    guest_id="ubuntu64Guest"
)
task_id = await vm_service.create_vm(vm_data)
```

### 3. 异步任务处理

```python
from app.services.task_service import TaskService
import asyncio

task_service = TaskService()

async def create_vm_task(task_id: str, vm_data: dict):
    try:
        # 执行创建任务
        await task_service.update_task(task_id, "running", None, None)
        result = await do_create_vm(vm_data)
        await task_service.update_task(task_id, "completed", result, None)
    except Exception as e:
        await task_service.update_task(task_id, "failed", None, str(e))

# 创建后台任务
task_id = await task_service.create_task("vm_create", vm_data.dict())
asyncio.create_task(create_vm_task(task_id, vm_data.dict()))
```

## 代码规范

### 后端规范

- 使用Type Hints
- 所有API使用Pydantic进行请求/响应校验
- 异步函数使用async/await
- 错误处理使用自定义异常类
- 日志使用Python logging模块

### 前端规范

- 使用Composition API
- 组件命名: PascalCase
- API响应使用TypeScript类型定义
- 使用Pinia进行状态管理

## 测试

### 后端测试

```bash
cd backend
pytest tests/ -v
```

### 前端测试

```bash
cd frontend
npm run test
```

## Docker部署

### 使用Docker Compose

```bash
cd docker
docker-compose up -d
```

### 手动构建

```bash
# 构建后端镜像
docker build -f backend.Dockerfile -t cloud-manager-backend .

# 构建前端镜像
docker build -f frontend.Dockerfile -t cloud-manager-frontend .

# 运行
docker-compose up -d
```

## 常见问题

### vSphere连接失败

1. 检查vCenter地址和端口
2. 验证用户名密码
3. 确认网络连通性
4. 检查SSL证书问题

### 权限不足

确保vSphere账户具有以下权限:
- VirtualMachine.Inventory.Create
- VirtualMachine.Inventory.Delete
- VirtualMachine.Config.Resource
- VirtualMachine.Config.ChangeTracking
- VirtualMachine.Provisioning.CreateTemplate
- VirtualMachine.Provisioning.DeployTemplate
- Task.Create
- Task.View

