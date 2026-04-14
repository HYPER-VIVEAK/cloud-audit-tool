import { api } from './client'
import type { CreateCredentialPayload, CredentialSummary } from './types'

export const fetchCredentials = async () => {
  const { data } = await api.get<CredentialSummary[]>('/credentials')
  return data
}

export const createCredential = async (payload: CreateCredentialPayload) => {
  const { data } = await api.post<CredentialSummary>('/credentials', payload)
  return data
}
