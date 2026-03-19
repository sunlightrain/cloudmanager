import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.vsphere import get_vsphere_client, VSphereOperationError
from app.models.datacenter import Datacenter
from app.models.cluster import Cluster
from app.models.host import Host
from app.models.vm import VM
from app.models.storage import Datastore
from app.models.network import Network

logger = logging.getLogger(__name__)


class IncrementalSyncService:
    _instance = None
    _lock = asyncio.Lock()
    _running = False
    _sync_interval = 60
    
    def __init__(self):
        self._tasks = {}
    
    @classmethod
    async def get_instance(cls) -> "IncrementalSyncService":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    async def start(self, session_factory, sync_interval: int = 60):
        if self._running:
            logger.warning("Incremental sync already running")
            return
        
        self._running = True
        self._sync_interval = sync_interval
        self._session_factory = session_factory
        
        logger.info(f"Starting incremental sync with interval {sync_interval}s")
        
        while self._running:
            try:
                await self._sync_once()
            except Exception as e:
                logger.error(f"Error during incremental sync: {e}")
            
            await asyncio.sleep(self._sync_interval)
    
    async def stop(self):
        self._running = False
        logger.info("Stopping incremental sync")
    
    async def _sync_once(self):
        from app.core.database import get_session
        
        session = next(get_session())
        try:
            inventory_service = InventoryService(session)
            inventory_service.sync_incremental()
            
            snapshot_service = SnapshotMonitorService(session)
            snapshot_service.check_long_running_snapshots()
            
            logger.debug("Incremental sync completed")
        finally:
            session.close()


class SnapshotMonitorService:
    SNAPSHOT_MAX_AGE_HOURS = 72
    
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    def check_long_running_snapshots(self) -> List[Dict[str, Any]]:
        alerts = []
        try:
            vms = self.session.query(VM).all()
            cutoff_time = datetime.utcnow() - timedelta(hours=self.SNAPSHOT_MAX_AGE_HOURS)
            
            for vm in vms:
                snapshots = self.vsphere.get_snapshots(vm.vc_guid)
                for snap in snapshots:
                    try:
                        created_str = snap.get("created")
                        if created_str:
                            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                            if created < cutoff_time:
                                alerts.append({
                                    "vm_id": vm.vc_guid,
                                    "vm_name": vm.name,
                                    "snapshot_id": snap.get("snapshot_id"),
                                    "snapshot_name": snap.get("name"),
                                    "created": created_str,
                                    "age_hours": (datetime.utcnow() - created).total_seconds() / 3600
                                })
                    except Exception as e:
                        logger.warning(f"Error checking snapshot {snap.get('snapshot_id')}: {e}")
            
            if alerts:
                logger.warning(f"Found {len(alerts)} long-running snapshots")
                self._save_alerts(alerts)
            
        except Exception as e:
            logger.error(f"Error checking long-running snapshots: {e}")
        
        return alerts
    
    def cleanup_old_snapshots(self, vm_id: str, keep_count: int = 0) -> Dict[str, Any]:
        try:
            snapshots = self.vsphere.get_snapshots(vm_id)
            if not snapshots:
                return {"success": True, "message": "No snapshots to clean"}
            
            snapshots_sorted = sorted(
                snapshots,
                key=lambda x: x.get("created", ""),
                reverse=True
            )
            
            to_delete = snapshots_sorted[keep_count:]
            deleted = []
            failed = []
            
            for snap in to_delete:
                try:
                    self.vsphere.delete_snapshot(vm_id, snap.get("snapshot_id"))
                    deleted.append(snap.get("name"))
                except Exception as e:
                    failed.append({"name": snap.get("name"), "error": str(e)})
            
            return {
                "success": len(failed) == 0,
                "deleted": deleted,
                "failed": failed,
                "message": f"Deleted {len(deleted)} snapshots"
            }
        except Exception as e:
            logger.error(f"Error cleaning up snapshots for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    def _save_alerts(self, alerts: List[Dict[str, Any]]):
        logger.warning(f"Snapshot alerts: {json.dumps(alerts)}")


class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    def sync_all(self) -> Dict[str, Any]:
        result = {
            "datacenters": 0,
            "clusters": 0,
            "hosts": 0,
            "vms": 0,
            "datastores": 0,
            "networks": 0,
            "errors": []
        }
        
        try:
            result["datacenters"] = self.sync_datacenters()
        except Exception as e:
            result["errors"].append(f"Datacenter sync failed: {e}")
        
        try:
            result["clusters"] = self.sync_clusters()
        except Exception as e:
            result["errors"].append(f"Cluster sync failed: {e}")
        
        try:
            result["hosts"] = self.sync_hosts()
        except Exception as e:
            result["errors"].append(f"Host sync failed: {e}")
        
        try:
            result["vms"] = self.sync_vms()
        except Exception as e:
            result["errors"].append(f"VM sync failed: {e}")
        
        try:
            result["datastores"] = self.sync_datastores()
        except Exception as e:
            result["errors"].append(f"Datastore sync failed: {e}")
        
        try:
            result["networks"] = self.sync_networks()
        except Exception as e:
            result["errors"].append(f"Network sync failed: {e}")
        
        return result
    
    def sync_incremental(self) -> Dict[str, Any]:
        result = {
            "vms": 0,
            "hosts": 0,
            "errors": []
        }
        
        try:
            result["hosts"] = self.sync_hosts_incremental()
        except Exception as e:
            result["errors"].append(f"Host incremental sync failed: {e}")
        
        try:
            result["vms"] = self.sync_vms_incremental()
        except Exception as e:
            result["errors"].append(f"VM incremental sync failed: {e}")
        
        return result
    
    def sync_hosts_incremental(self) -> int:
        count = 0
        try:
            host_list = self.vsphere.get_hosts()
            existing_guids = {h.vc_guid for h in self.session.query(Host).all()}
            
            for host_data in host_list:
                host_id = host_data.get("host_id")
                
                if host_id in existing_guids:
                    host = self.session.query(Host).filter(Host.vc_guid == host_id).first()
                    if host:
                        host.name = host_data.get("name", host.name)
                        host.status = host_data.get("status", host.status)
                        host.connection_state = host_data.get("connection_state", host.connection_state)
                        host.maintenance_mode = host_data.get("maintenance_mode", host.maintenance_mode)
                        host.last_sync = datetime.utcnow()
                count += 1
            
            self.session.commit()
        except Exception as e:
            logger.error(f"Error in host incremental sync: {e}")
            self.session.rollback()
        
        return count
    
    def sync_vms_incremental(self) -> int:
        count = 0
        try:
            vm_list = self.vsphere.get_vms()
            existing_guids = {vm.vc_guid for vm in self.session.query(VM).all()}
            
            for vm_data in vm_list:
                vm_id = vm_data.get("vm_id")
                
                if vm_id in existing_guids:
                    vm = self.session.query(VM).filter(VM.vc_guid == vm_id).first()
                    if vm:
                        vm.name = vm_data.get("name", vm.name)
                        vm.status = vm_data.get("status", vm.status)
                        vm.last_sync = datetime.utcnow()
                count += 1
            
            self.session.commit()
        except Exception as e:
            logger.error(f"Error in VM incremental sync: {e}")
            self.session.rollback()
        
        return count
    
    def sync_datacenters(self) -> int:
        count = 0
        dc_list = self.vsphere.get_datacenters()
        
        for dc_data in dc_list:
            existing = self.session.query(Datacenter).filter(
                Datacenter.vc_guid == dc_data["dc_id"]
            ).first()
            
            if existing:
                existing.name = dc_data["name"]
                existing.raw_data = json.dumps(dc_data)
                existing.last_sync = datetime.utcnow()
            else:
                dc = Datacenter(
                    vc_guid=dc_data["dc_id"],
                    name=dc_data["name"],
                    raw_data=json.dumps(dc_data),
                    last_sync=datetime.utcnow()
                )
                self.session.add(dc)
            count += 1
        
        self.session.commit()
        logger.info(f"Synced {count} datacenters")
        return count
    
    def sync_clusters(self) -> int:
        count = 0
        cluster_list = self.vsphere.get_clusters()
        
        for cluster_data in cluster_list:
            existing = self.session.query(Cluster).filter(
                Cluster.vc_guid == cluster_data["cluster_id"]
            ).first()
            
            datacenter = self.session.query(Datacenter).first()
            datacenter_id = datacenter.id if datacenter else 0
            
            if existing:
                existing.name = cluster_data["name"]
                existing.host_count = cluster_data.get("host_count", 0)
                existing.total_cpu_cores = cluster_data.get("total_cpu_cores", 0)
                existing.total_memory_gb = cluster_data.get("total_memory_gb", 0)
                existing.raw_data = json.dumps(cluster_data)
                existing.last_sync = datetime.utcnow()
            else:
                cluster = Cluster(
                    vc_guid=cluster_data["cluster_id"],
                    datacenter_id=datacenter_id,
                    name=cluster_data["name"],
                    host_count=cluster_data.get("host_count", 0),
                    total_cpu_cores=cluster_data.get("total_cpu_cores", 0),
                    total_memory_gb=cluster_data.get("total_memory_gb", 0),
                    raw_data=json.dumps(cluster_data),
                    last_sync=datetime.utcnow()
                )
                self.session.add(cluster)
            count += 1
        
        self.session.commit()
        logger.info(f"Synced {count} clusters")
        return count
    
    def sync_hosts(self) -> int:
        count = 0
        host_list = self.vsphere.get_hosts()
        
        for host_data in host_list:
            existing = self.session.query(Host).filter(
                Host.vc_guid == host_data["host_id"]
            ).first()
            
            datacenter = self.session.query(Datacenter).first()
            datacenter_id = datacenter.id if datacenter else 0
            
            if existing:
                existing.name = host_data["name"]
                existing.status = host_data.get("status", "unknown")
                existing.connection_state = host_data.get("connection_state", "disconnected")
                existing.maintenance_mode = host_data.get("maintenance_mode", False)
                existing.last_sync = datetime.utcnow()
            else:
                host = Host(
                    vc_guid=host_data["host_id"],
                    datacenter_id=datacenter_id,
                    name=host_data["name"],
                    status=host_data.get("status", "unknown"),
                    connection_state=host_data.get("connection_state", "disconnected"),
                    maintenance_mode=host_data.get("maintenance_mode", False),
                    last_sync=datetime.utcnow()
                )
                self.session.add(host)
            count += 1
        
        self.session.commit()
        logger.info(f"Synced {count} hosts")
        return count
    
    def sync_vms(self) -> int:
        count = 0
        vm_list = self.vsphere.get_vms()
        
        for vm_data in vm_list:
            existing = self.session.query(VM).filter(
                VM.vc_guid == vm_data["vm_id"]
            ).first()
            
            datacenter = self.session.query(Datacenter).first()
            datacenter_id = datacenter.id if datacenter else 0
            
            if existing:
                existing.name = vm_data["name"]
                existing.status = vm_data.get("status", "unknown")
                existing.cpu = vm_data.get("cpu", 0)
                existing.memory_mb = vm_data.get("memory_mb", 0)
                existing.last_sync = datetime.utcnow()
            else:
                vm = VM(
                    vc_guid=vm_data["vm_id"],
                    datacenter_id=datacenter_id,
                    name=vm_data["name"],
                    status=vm_data.get("status", "unknown"),
                    cpu=vm_data.get("cpu", 0),
                    memory_mb=vm_data.get("memory_mb", 0),
                    ip_addresses=json.dumps([vm_data.get("ip_address")]) if vm_data.get("ip_address") else None,
                    last_sync=datetime.utcnow()
                )
                self.session.add(vm)
            count += 1
        
        self.session.commit()
        logger.info(f"Synced {count} VMs")
        return count
    
    def sync_datastores(self) -> int:
        count = 0
        ds_list = self.vsphere.get_datastores()
        
        for ds_data in ds_list:
            existing = self.session.query(Datastore).filter(
                Datastore.vc_guid == ds_data["datastore_id"]
            ).first()
            
            datacenter = self.session.query(Datacenter).first()
            datacenter_id = datacenter.id if datacenter else 0
            
            capacity_gb = ds_data.get("capacity_gb", 0)
            free_gb = ds_data.get("free_gb", 0)
            used_percent = ((capacity_gb - free_gb) / capacity_gb * 100) if capacity_gb > 0 else 0
            
            if existing:
                existing.name = ds_data["name"]
                existing.type = ds_data.get("type", "unknown")
                existing.capacity_gb = capacity_gb
                existing.free_gb = free_gb
                existing.used_percent = used_percent
                existing.raw_data = json.dumps(ds_data)
                existing.last_sync = datetime.utcnow()
            else:
                datastore = Datastore(
                    vc_guid=ds_data["datastore_id"],
                    datacenter_id=datacenter_id,
                    name=ds_data["name"],
                    type=ds_data.get("type", "unknown"),
                    capacity_gb=capacity_gb,
                    free_gb=free_gb,
                    used_percent=used_percent,
                    raw_data=json.dumps(ds_data),
                    last_sync=datetime.utcnow()
                )
                self.session.add(datastore)
            count += 1
        
        self.session.commit()
        logger.info(f"Synced {count} datastores")
        return count
    
    def sync_networks(self) -> int:
        count = 0
        network_list = self.vsphere.get_networks()
        
        for network_data in network_list:
            existing = self.session.query(Network).filter(
                Network.vc_guid == network_data["network_id"]
            ).first()
            
            datacenter = self.session.query(Datacenter).first()
            datacenter_id = datacenter.id if datacenter else 0
            
            if existing:
                existing.name = network_data["name"]
                existing.type = network_data.get("type", "Standard")
                existing.raw_data = json.dumps(network_data)
                existing.last_sync = datetime.utcnow()
            else:
                network = Network(
                    vc_guid=network_data["network_id"],
                    datacenter_id=datacenter_id,
                    name=network_data["name"],
                    type=network_data.get("type", "Standard"),
                    raw_data=json.dumps(network_data),
                    last_sync=datetime.utcnow()
                )
                self.session.add(network)
            count += 1
        
        self.session.commit()
        logger.info(f"Synced {count} networks")
        return count
    
    def get_datacenters(self) -> List[Datacenter]:
        return self.session.query(Datacenter).all()
    
    def get_clusters(self, datacenter_id: Optional[int] = None) -> List[Cluster]:
        query = self.session.query(Cluster)
        if datacenter_id:
            query = query.filter(Cluster.datacenter_id == datacenter_id)
        return query.all()
    
    def get_hosts(self, cluster_id: Optional[int] = None) -> List[Host]:
        query = self.session.query(Host)
        if cluster_id:
            query = query.filter(Host.cluster_id == cluster_id)
        return query.all()
    
    def get_vms(self, host_id: Optional[int] = None, status: Optional[str] = None) -> List[VM]:
        query = self.session.query(VM)
        if host_id:
            query = query.filter(VM.host_id == host_id)
        if status:
            query = query.filter(VM.status == status)
        return query.all()
    
    def get_datastores(self, datacenter_id: Optional[int] = None) -> List[Datastore]:
        query = self.session.query(Datastore)
        if datacenter_id:
            query = query.filter(Datastore.datacenter_id == datacenter_id)
        return query.all()
    
    def get_networks(self, datacenter_id: Optional[int] = None) -> List[Network]:
        query = self.session.query(Network)
        if datacenter_id:
            query = query.filter(Network.datacenter_id == datacenter_id)
        return query.all()
    
    def get_overview(self) -> Dict[str, Any]:
        vms = self.session.query(VM).all()
        hosts = self.session.query(Host).all()
        datastores = self.session.query(Datastore).all()
        
        powered_on = sum(1 for vm in vms if vm.status == "poweredOn")
        powered_off = sum(1 for vm in vms if vm.status == "poweredOff")
        
        total_memory_gb = sum(host.memory_gb for host in hosts)
        total_storage_tb = sum(ds.capacity_gb for ds in datastores) / 1024
        used_storage_tb = sum(ds.used_gb for ds in datastores) / 1024
        
        return {
            "total_hosts": len(hosts),
            "total_vms": len(vms),
            "vm_by_status": {
                "poweredOn": powered_on,
                "poweredOff": powered_off
            },
            "total_memory_gb": round(total_memory_gb, 2),
            "total_storage_tb": round(total_storage_tb, 2),
            "used_storage_tb": round(used_storage_tb, 2),
            "used_storage_percent": round((used_storage_tb / total_storage_tb * 100) if total_storage_tb > 0 else 0, 1),
            "datastore_count": len(datastores),
        }
