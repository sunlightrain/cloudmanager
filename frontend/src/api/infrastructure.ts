import api from './index'

export interface Datastore {
  datastore_id: string
  name: string
  type: string
  capacity_gb: number
  free_gb: number
  used_percent: number
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
  total_cpu_cores: number
  total_memory_gb: number
}

export interface InfrastructureApi {
  getDatastores: () => Promise<any>
  getNetworks: () => Promise<any>
  getClusters: () => Promise<any>
  getDatacenters: () => Promise<any>
  getHostDetail: (hostId: string) => Promise<any>
}

export const infraApi: InfrastructureApi = {
  getDatastores: () => api.get('/infrastructure/datastores'),
  getNetworks: () => api.get('/infrastructure/networks'),
  getClusters: () => api.get('/infrastructure/clusters'),
  getDatacenters: () => api.get('/infrastructure/datacenters'),
  getHostDetail: (hostId: string) => api.get(`/infrastructure/hosts/${hostId}`)
}
