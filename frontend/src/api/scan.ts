import { api } from './client'
import type { RunScanPayload, ScanHistoryResponse, ScanRunResponse, ScanSummaryResponse } from './types'

export const runScan = async (payload: RunScanPayload) => {
  const { data } = await api.post<ScanRunResponse>('/scan/run', payload)
  return data
}

export const fetchScanSummary = async () => {
  const { data } = await api.get<ScanSummaryResponse>('/scan/summary')
  return data
}

export const fetchScanHistory = async () => {
  const { data } = await api.get<ScanHistoryResponse>('/scan/history')
  return data
}
