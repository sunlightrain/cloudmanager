import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.core.vsphere import get_vsphere_client, VSphereOperationError
from app.models.cluster import Cluster

logger = logging.getLogger(__name__)


class ClusterService:
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    def get_ha_status(self, cluster_id: str) -> Dict[str, Any]:
        try:
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return {"enabled": False, "error": "Cluster not found"}
            
            if hasattr(cluster, 'configurationEx'):
                config = cluster.configurationEx
                return {
                    "enabled": hasattr(config, 'dasConfig') and config.dasConfig.enabled if config else False,
                    "admission_control": self._get_das_admission_control(config) if config else None,
                    "host_monitoring": self._get_das_host_monitoring(config) if config else None,
                    "vm_monitoring": self._get_das_vm_monitoring(config) if config else None,
                }
            
            return {"enabled": False}
        except Exception as e:
            logger.error(f"Error getting HA status for cluster {cluster_id}: {e}")
            return {"enabled": False, "error": str(e)}
    
    def get_drs_status(self, cluster_id: str) -> Dict[str, Any]:
        try:
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return {"enabled": False, "error": "Cluster not found"}
            
            if hasattr(cluster, 'configurationEx'):
                config = cluster.configurationEx
                return {
                    "enabled": hasattr(config, 'drsConfig') and config.drsConfig.enabled if config else False,
                    "automation_level": self._get_drs_automation_level(config) if config else None,
                    "vmotion_rate": config.drsConfig.vmotionRate if config and hasattr(config, 'drsConfig') and hasattr(config.drsConfig, 'vmotionRate') else None,
                }
            
            return {"enabled": False}
        except Exception as e:
            logger.error(f"Error getting DRS status for cluster {cluster_id}: {e}")
            return {"enabled": False, "error": str(e)}
    
    def get_drs_recommendations(self, cluster_id: str) -> List[Dict[str, Any]]:
        try:
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return []
            
            recommendations = []
            if hasattr(cluster, 'recommendation'):
                for rec in cluster.recommendation:
                    recommendations.append({
                        "key": rec.key,
                        "type": rec.type,
                        "message": rec.message,
                        "target_vm": rec.target._GetMoId() if hasattr(rec, 'target') and rec.target else None,
                        "priority": rec.priority,
                    })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting DRS recommendations for cluster {cluster_id}: {e}")
            return []
    
    def apply_drs_recommendation(self, cluster_id: str, recommendation_key: str) -> Dict[str, Any]:
        try:
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return {"success": False, "message": "Cluster not found"}
            
            if hasattr(cluster, 'ApplyRecommendation'):
                cluster.ApplyRecommendation(recommendation_key)
                return {"success": True, "message": "Recommendation applied"}
            
            return {"success": False, "message": "ApplyRecommendation not supported"}
        except Exception as e:
            logger.error(f"Error applying DRS recommendation: {e}")
            return {"success": False, "message": str(e)}
    
    def _find_cluster_by_id(self, cluster_id: str):
        try:
            content = self.vsphere._client.content
            clusters = content.rootFolder.childEntity[0].hostFolder.childEntity
            for cluster in clusters:
                if cluster._GetMoId() == cluster_id:
                    return cluster
            return None
        except Exception as e:
            logger.error(f"Error finding cluster {cluster_id}: {e}")
            return None
    
    def _get_das_admission_control(self, config) -> Optional[Dict[str, Any]]:
        if not hasattr(config, 'dasConfig') or not config.dasConfig:
            return None
        
        das = config.dasConfig
        return {
            "enabled": das.enabled,
            "admission_control_policy": das.admissionControlPolicy.__class__.__name__ if hasattr(das, 'admissionControlPolicy') and das.admissionControlPolicy else None,
        }
    
    def _get_das_host_monitoring(self, config) -> Optional[str]:
        if not hasattr(config, 'dasConfig') or not config.dasConfig:
            return None
        return config.dasConfig.hostMonitoring if hasattr(config.dasConfig, 'hostMonitoring') else None
    
    def _get_das_vm_monitoring(self, config) -> Optional[str]:
        if not hasattr(config, 'dasConfig') or not config.dasConfig:
            return None
        return config.dasConfig.vmMonitoring if hasattr(config.dasConfig, 'vmMonitoring') else None
    
    def _get_drs_automation_level(self, config) -> Optional[str]:
        if not hasattr(config, 'drsConfig') or not config.drsConfig:
            return None
        return config.drsConfig.defaultVmBehavior if hasattr(config.drsConfig, 'defaultVmBehavior') else None
    
    def get_drs_rules(self, cluster_id: str) -> List[Dict[str, Any]]:
        try:
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return []
            
            rules = []
            if hasattr(cluster, 'configurationEx') and hasattr(cluster.configurationEx, 'drsRules'):
                for rule in cluster.configurationEx.drsRules:
                    rules.append({
                        "rule_id": rule.key,
                        "name": rule.name,
                        "enabled": rule.enabled,
                        "type": rule.type if hasattr(rule, 'type') else None,
                        "vm_ids": [vm._GetMoId() for vm in rule.vm] if hasattr(rule, 'vm') else [],
                    })
            
            return rules
        except Exception as e:
            logger.error(f"Error getting DRS rules for cluster {cluster_id}: {e}")
            return []
    
    def create_drs_rule(
        self,
        cluster_id: str,
        name: str,
        vm_ids: List[str],
        rule_type: str = "affinity",
        enabled: bool = True
    ) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return {"success": False, "message": "Cluster not found"}
            
            vms = []
            for vm_id in vm_ids:
                vm = self.vsphere._find_vm(vm_id)
                if vm:
                    vms.append(vm)
            
            if rule_type == "affinity":
                spec = vim.cluster.AffinityRuleSpec()
            elif rule_type == "anti-affinity":
                spec = vim.cluster.AntiAffinityRuleSpec()
            else:
                return {"success": False, "message": f"Unsupported rule type: {rule_type}"}
            
            spec.name = name
            spec.enabled = enabled
            spec.vm = vms
            
            cluster_info = cluster.configurationEx
            rules = list(cluster_info.drsRules) if cluster_info.drsRules else []
            rules.append(spec)
            
            config_spec = vim.cluster.ConfigSpecEx()
            config_spec.drsRules = rules
            
            task = cluster.ReconfigureComputeResource_Task(config_spec, modify=True)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": f"DRS rule '{name}' created"}
        except Exception as e:
            logger.error(f"Error creating DRS rule: {e}")
            return {"success": False, "message": str(e)}
    
    def delete_drs_rule(self, cluster_id: str, rule_key: int) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return {"success": False, "message": "Cluster not found"}
            
            cluster_info = cluster.configurationEx
            rules = [r for r in cluster_info.drsRules if r.key != rule_key] if cluster_info.drsRules else []
            
            config_spec = vim.cluster.ConfigSpecEx()
            config_spec.drsRules = rules
            
            task = cluster.ReconfigureComputeResource_Task(config_spec, modify=True)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "DRS rule deleted"}
        except Exception as e:
            logger.error(f"Error deleting DRS rule: {e}")
            return {"success": False, "message": str(e)}
    
    def get_resource_pools(self, cluster_id: str) -> List[Dict[str, Any]]:
        try:
            cluster = self._find_cluster_by_id(cluster_id)
            if not cluster:
                return []
            
            pools = []
            if hasattr(cluster, 'resourcePool'):
                pools = self._flatten_resource_pools(cluster.resourcePool, [])
            
            return pools
        except Exception as e:
            logger.error(f"Error getting resource pools for cluster {cluster_id}: {e}")
            return []
    
    def _flatten_resource_pools(self, pool, result: List[Dict[str, Any]], parent_path: str = "") -> List[Dict[str, Any]]:
        try:
            for child in pool:
                if hasattr(child, 'name'):
                    path = f"{parent_path}/{child.name}" if parent_path else child.name
                    pool_info = {
                        "id": child._GetMoId(),
                        "name": child.name,
                        "path": path,
                        "cpu_limit": child.config.cpuAllocation.limit if hasattr(child, 'config') and hasattr(child.config, 'cpuAllocation') else -1,
                        "cpu_reservation": child.config.cpuAllocation.reservation if hasattr(child, 'config') and hasattr(child.config, 'cpuAllocation') else 0,
                        "memory_limit": child.config.memoryAllocation.limit if hasattr(child, 'config') and hasattr(child.config, 'memoryAllocation') else -1,
                        "memory_reservation": child.config.memoryAllocation.reservation if hasattr(child, 'config') and hasattr(child.config, 'memoryAllocation') else 0,
                    }
                    result.append(pool_info)
                    
                    if hasattr(child, 'resourcePool'):
                        self._flatten_resource_pools(child.resourcePool, result, path)
        except Exception as e:
            logger.warning(f"Error flattening resource pool: {e}")
        
        return result
    
    def update_resource_pool(
        self,
        pool_id: str,
        cpu_limit: int = None,
        cpu_reservation: int = None,
        memory_limit: int = None,
        memory_reservation: int = None
    ) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            pool = self._find_resource_pool_by_id(pool_id)
            if not pool:
                return {"success": False, "message": "Resource pool not found"}
            
            config_spec = vim.ResourceConfigSpec()
            
            if cpu_limit is not None or cpu_reservation is not None:
                cpu_allocation = vim.ResourceAllocationInfo()
                if cpu_limit is not None:
                    cpu_allocation.limit = cpu_limit
                if cpu_reservation is not None:
                    cpu_allocation.reservation = cpu_reservation
                config_spec.cpuAllocation = cpu_allocation
            
            if memory_limit is not None or memory_reservation is not None:
                memory_allocation = vim.ResourceAllocationInfo()
                if memory_limit is not None:
                    memory_allocation.limit = memory_limit
                if memory_reservation is not None:
                    memory_allocation.reservation = memory_reservation
                config_spec.memoryAllocation = memory_allocation
            
            pool.UpdateConfig(config_spec)
            
            return {"success": True, "message": "Resource pool updated"}
        except Exception as e:
            logger.error(f"Error updating resource pool: {e}")
            return {"success": False, "message": str(e)}
    
    def _find_resource_pool_by_id(self, pool_id: str):
        try:
            content = self.vsphere._client.content
            clusters = content.rootFolder.childEntity[0].hostFolder.childEntity
            
            for cluster in clusters:
                if hasattr(cluster, 'resourcePool'):
                    found = self._search_resource_pool(cluster.resourcePool, pool_id)
                    if found:
                        return found
            return None
        except Exception as e:
            logger.error(f"Error finding resource pool {pool_id}: {e}")
            return None
    
    def _search_resource_pool(self, pools, pool_id: str):
        for pool in pools:
            if pool._GetMoId() == pool_id:
                return pool
            if hasattr(pool, 'resourcePool'):
                found = self._search_resource_pool(pool.resourcePool, pool_id)
                if found:
                    return found
        return None


class FaultToleranceService:
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    def get_ft_status(self, vm_id: str) -> Dict[str, Any]:
        try:
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"enabled": False, "error": "VM not found"}
            
            if not hasattr(vm, 'config') or not hasattr(vm.config, 'faultTolerance'):
                return {"enabled": False}
            
            ft_info = vm.config.faultTolerance
            return {
                "enabled": ft_info.faultToleranceEnabled if hasattr(ft_info, 'faultToleranceEnabled') else False,
                "role": ft_info.role if hasattr(ft_info, 'role') else None,
                "secondary_vm": ft_info.secondary_vm._GetMoId() if hasattr(ft_info, 'secondary_vm') and ft_info.secondary_vm else None,
            }
        except Exception as e:
            logger.error(f"Error getting FT status for VM {vm_id}: {e}")
            return {"enabled": False, "error": str(e)}
    
    def enable_ft(self, vm_id: str) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            if vm.runtime.powerState.value != "poweredOn":
                return {"success": False, "message": "VM must be powered on for FT"}
            
            if hasattr(vm, 'CreateSecondaryVM_Task'):
                task = vm.CreateSecondaryVM_Task()
                self.vsphere._wait_for_task(task)
                return {"success": True, "message": "Fault Tolerance enabled"}
            
            return {"success": False, "message": "FT not supported on this VM"}
        except Exception as e:
            logger.error(f"Error enabling FT for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    def disable_ft(self, vm_id: str) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            if hasattr(vm, 'TerminateFaultTolerantVM_Task'):
                task = vm.TerminateFaultTolerantVM_Task()
                self.vsphere._wait_for_task(task)
                return {"success": True, "message": "Fault Tolerance disabled"}
            
            return {"success": False, "message": "FT not enabled on this VM"}
        except Exception as e:
            logger.error(f"Error disabling FT for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
