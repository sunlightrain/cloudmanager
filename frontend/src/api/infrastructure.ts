import api from './index'

export interface Datastore {
  datastore_id: string
  name: string
  type: string
  capacity_gb: number
  free_gb: number
  used_percent: number
  used_gb?: number
}

export interface Network {
  network_id: string
  name: string
  type: string
}

export interface Cluster {
  cluster_id: string
  name: string
  host_count: number
  cpu_total_mhz?: number
  cpu_usage_percent?: number
  mem_total_gb?: number
  mem_usage_percent?: number
  drs_enabled?: boolean
  ha_enabled?: boolean
}

export interface DatacenterTree {
  id: string
  name: string
  type: string
  children?: DatacenterTree[]
  cpu?: { model?: string; cores?: number }
  memory?: { total_gb?: number }
  stats?: { cpu_usage_percent?: number; memory_usage_gb?: number }
  datastores?: { id: string; name: string }[]
  networks?: { id: string; name: string }[]
}

export interface DatacenterOverview {
  datacenter: { id: string; name: string }
  clusters: { count: number; items: Cluster[] }
  hosts: { total: number; powered_on: number; maintenance_mode: number }
  vms: { total: number; powered_on: number; powered_off: number }
  storage: {
    total_gb: number
    free_gb: number
    used_gb: number
    usage_percent: number
  }
  compute: { total_cpu_cores: number; total_memory_gb: number }
  features: { ha_enabled: boolean; drs_enabled: boolean }
}

export interface Host {
  host_id: string
  name: string
  status: string
  power_state: string
  maintenance_mode: boolean
  cpu?: { model: string; cores: number }
  memory?: { total_gb: number }
  stats?: { cpu_usage_percent: number; memory_usage_gb: number }
  cpu_usage_percent?: number
  memory_usage_gb?: number
}

export interface StorageOverview {
  total_datastores: number
  total_capacity_gb: number
  total_free_gb: number
  total_used_gb: number
  usage_percent: number
  by_type: Record<string, { count: number; total_gb: number; free_gb: number }>
  datastores: Datastore[]
}

export interface NetworkOverview {
  total_networks: number
  standard_switches: { count: number; items: any[] }
  distributed_switches: { count: number; items: any[] }
  port_groups: { count: number; items: any[] }
}

export const infraApi = {
  getDatastores: () => api.get('/storage/datastores'),
  getStorageOverview: () => api.get('/storage/datastores/overview'),
  getDatastore: (id: string) => api.get(`/storage/datastores/${id}`),
  
  getNetworks: () => api.get('/networks'),
  getNetworkOverview: () => api.get('/networks/overview'),
  getStandardSwitches: () => api.get('/networks/standard-switches'),
  getDistributedSwitches: () => api.get('/networks/distributed-switches'),
  getPortGroups: () => api.get('/networks/port-groups'),
  
  getClusters: () => api.get('/clusters'),
  getCluster: (id: string) => api.get(`/clusters/${id}`),
  getClusterHosts: (id: string) => api.get(`/clusters/${id}/hosts`),
  getClusterHA: (id: string) => api.get(`/clusters/${id}/ha`),
  getClusterDRS: (id: string) => api.get(`/clusters/${id}/drs`),
  getClusterResourcePools: (id: string) => api.get(`/clusters/${id}/resource-pools`),
  
  getDatacenters: () => api.get('/datacenters'),
  getDatacenterTree: () => api.get('/datacenters/tree'),
  getDatacenterOverview: (name: string) => api.get(`/datacenters/${name}/overview`),
  
  getHosts: (datacenter?: string) => api.get('/hosts', { params: { datacenter } }),
  getHostsOverview: (datacenter?: string) => api.get('/hosts/overview', { params: { datacenter } }),
  getHost: (id: string) => api.get(`/hosts/${id}`),
  getHostVMs: (id: string) => api.get(`/hosts/${id}/vms`),
  
  vmotionPrecheck: (data: { vm_id: string; target_host_id?: string; target_cluster_id?: string }) => 
    api.post('/migration/vmotion/precheck', data),
  executeVMotion: (data: { vm_id: string; target_host_id?: string; target_cluster_id?: string; priority?: string }) => 
    api.post('/migration/vmotion', data),
  executeStorageVMotion: (data: { vm_id: string; target_datastore_name: string }) => 
    api.post('/migration/storage-vmotion', data),
}
