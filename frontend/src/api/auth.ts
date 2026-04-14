import { api } from './client'
import type { CreateUserPayload, LoginResponse, MeResponse, UserSummary } from './types'

export const login = async (username: string, password: string) => {
  const { data } = await api.post<LoginResponse>('/auth/login', { username, password })
  return data
}

export const fetchMe = async () => {
  const { data } = await api.get<MeResponse>('/auth/me')
  return data
}

export const refresh = async () => {
  const { data } = await api.post<LoginResponse>('/auth/refresh')
  return data
}

export const logout = async () => {
  await api.post('/auth/logout')
}

export const fetchUsers = async () => {
  const { data } = await api.get<UserSummary[]>('/auth/users')
  return data
}

export const createUser = async (payload: CreateUserPayload) => {
  const { data } = await api.post<UserSummary>('/auth/users', payload)
  return data
}
