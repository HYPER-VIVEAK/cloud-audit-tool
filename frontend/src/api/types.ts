export type LoginResponse = {
  message: string
  username: string
  role: string
  scope: string[]
}

export type MeResponse = {
  username: string
  role: string
  scope: string[]
}

export type UserSummary = {
  id: number
  username: string
  role: string
  created_at: string | null
  scope: string[]
}

export type CreateUserPayload = {
  username: string
  password: string
  role: 'admin' | 'user'
}

export type CredentialSummary = {
  id: number
  user_id: number
  platform: string
  environment: string
  region: string | null
  access_key_id: string
  created_at: string | null
  last_used: string | null
}

export type CreateCredentialPayload = {
  platform: 'AWS' | 'AZURE' | 'GCP'
  environment: string
  region?: string
  access_key_id: string
  secret_key: string
}

export type ScanReportPaths = {
  html: string
  json: string
}

export type ScanAnalysis = Record<string, unknown>

export type ScanRunResponse = {
  analysis: ScanAnalysis
  reports: ScanReportPaths
  stored_scan_id: string
}

export type RunScanPayload = {
  platform: 'AWS' | 'AZURE' | 'GCP'
  credential_id: number
}

export type ScanSummaryResponse = {
  analysis: ScanAnalysis | null
}

export type ScanHistoryItem = {
  id: string
  metadata: {
    user_id: number
    platform: string
    environment: string
    credential_id?: number | null
    scan_time: string | null
  }
  summary: {
    total_checks?: number
    passed?: number
    failed?: number
    severity_counts?: {
      critical?: number
      high?: number
      medium?: number
      low?: number
    }
  }
  findings: Array<{
    resource?: string
    issue?: string
    severity?: string
    remediation?: string
  }>
}

export type ScanHistoryResponse = {
  results: ScanHistoryItem[]
}

export type IAMUser = {
  user_name?: string
  arn?: string
  created?: string
}

export type S3Bucket = {
  name?: string
  created?: string
}

export type EC2Instance = {
  instance_id?: string
  type?: string
  state?: string
  public_ip?: string
  private_ip?: string
  tags?: { Key?: string; Value?: string }[]
}

export type UsersResponse = { users: IAMUser[] }
export type BucketsResponse = { buckets: S3Bucket[] }
export type InstancesResponse = { instances: EC2Instance[] }
