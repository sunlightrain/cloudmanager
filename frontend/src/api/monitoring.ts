import api from './index'

export interface AlertRule {
  id: number
  name: string
  resource_type: string
  metric: string
  condition: string
  threshold: number
  duration: number
  severity: 'info' | 'warning' | 'critical'
  is_active: boolean
}

export interface Alert {
  id: number
  rule_id: number
  tenant_id: number
  resource_type: string
  resource_id: string
  metric: string
  value: number
  threshold: number
  severity: string
  status: 'active' | 'acknowledged' | 'resolved'
  triggered_at: string
  acknowledged_at: string
  acknowledged_by: number
}

export interface MetricDataPoint {
  value: number
  timestamp: string
}

export const monitoringApi = {
  getAlerts: (params?: { tenant_id?: number; status?: string; severity?: string; limit?: number }) =>
    api.get('/monitoring/alerts', { params }),
  
  acknowledgeAlert: (alertId: number) => 
    api.post(`/monitoring/alerts/${alertId}/acknowledge`),
  
  resolveAlert: (alertId: number) => 
    api.post(`/monitoring/alerts/${alertId}/resolve`),
  
  getAlertRules: (resourceType?: string) =>
    api.get('/monitoring/alerts/rules', { params: resourceType ? { resource_type: resourceType } : {} }),
  
  createAlertRule: (data: Partial<AlertRule>) =>
    api.post('/monitoring/alerts/rules', null, { params: data }),
  
  getMetrics: (
    resourceType: string,
    resourceId: string,
    metric: string,
    params?: { start_time?: string; end_time?: string; limit?: number }
  ) => api.get(`/monitoring/metrics/${resourceType}/${resourceId}`, { 
    params: { metric, ...params } 
  }),
  
  createNotificationChannel: (data: { name: string; channel_type: string; config: any }) =>
    api.post('/monitoring/notifications/channels', data),
}
