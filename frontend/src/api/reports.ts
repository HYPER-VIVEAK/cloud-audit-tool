import { api } from './client'

export const buildPdfReportUrl = (scanId: string) => {
  const base = (api.defaults.baseURL ?? '').replace(/\/$/, '')
  return `${base}/scan/${scanId}/report/pdf`
}
