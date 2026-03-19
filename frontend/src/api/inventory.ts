import api from './index'

export interface Datacenter {
  id: number
  vc_guid: string
  name: string
  last_sync: string
}

export interface Cluster {
  id: number
  vc_guid: string
  name: string
  host_count: number
  total_cpu_cores: number
  total_memory_gb: number
  ha_enabled: boolean
  drs_enabled: boolean
}

export interface Host {
  id: number
  vc_guid: string
  name: string
  status: string
  connection_state: string
  maintenance_mode: boolean
  cpu_cores: number
  memory_gb: number
}

export interface Datastore {
  id: number
  vc_guid: string
  name: string
  type: string
  capacity_gb: number
  free_gb: number
  used_percent: number
}

export interface Network {
  id: number
  vc_guid: string
  name: string
  type: string
  vlan_id?: number
}

export interface Overview {
  total_hosts: number
  total_vms: number
  vm_by_status: {
    poweredOn: number
    poweredOff: number
  }
  total_memory_gb: number
  total_storage_tb: number
  used_storage_tb: number
  used_storage_percent: number
  datastore_count: number
}

export const inventoryApi = {
  sync: () => api.post('/inventory/sync'),
  
  getOverview: () => api.get('/inventory/overview'),
  
  getDatacenters: (datacenterId?: number) =>
    api.get('/inventory/datacenters', { params: { datacenter_id: datacenterId } }),
  
  getClusters: (datacenterId?: number) =>
    api.get('/inventory/clusters', { params: { datacenter_id: datacenterId } }),
  
  getHosts: (clusterId?: number) =>
    api.get('/inventory/hosts', { params: { cluster_id: clusterId } }),
  
  getVms: (hostId?: number, status?: string) =>
    api.get('/inventory/vms', { params: { host_id: hostId, status } }),
  
  getDatastores: (datacenterId?: number) =>
    api.get('/inventory/datastores', { params: { datacenter_id: datacenterId } }),
  
  getNetworks: (datacenterId?: number) =>
    api.get('/inventory/networks', { params: { datacenter_id: datacenterId } }),
}
