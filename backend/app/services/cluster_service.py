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
