import { api } from './client'
import type { BucketsResponse, InstancesResponse, UsersResponse } from './types'

export const listUsers = async (scanId?: string | null) => {
  const { data } = await api.get<UsersResponse>('/resources/iam/users', {
    params: scanId ? { scan_id: scanId } : undefined,
  })
  return data
}

export const listBuckets = async (scanId?: string | null) => {
  const { data } = await api.get<BucketsResponse>('/resources/s3/buckets', {
    params: scanId ? { scan_id: scanId } : undefined,
  })
  return data
}

export const listInstances = async (scanId?: string | null) => {
  const { data } = await api.get<InstancesResponse>('/resources/ec2/instances', {
    params: scanId ? { scan_id: scanId } : undefined,
  })
  return data
}
