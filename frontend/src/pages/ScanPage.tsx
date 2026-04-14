import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  PasswordInput,
  Select,
  Stack,
  Tabs,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useMutation, useQuery } from '@tanstack/react-query'
import { IconAlertCircle, IconFileText, IconPlayerPlay } from '@tabler/icons-react'
import { useState } from 'react'
import { createCredential, fetchCredentials } from '../api/credentials'
import { fetchScanHistory, runScan } from '../api/scan'
import type { CreateCredentialPayload } from '../api/types'

const blankCredentialForm: CreateCredentialPayload = {
  platform: 'AWS',
  environment: 'Prod',
  region: 'us-east-1',
  access_key_id: '',
  secret_key: '',
}

export const ScanPage: React.FC = () => {
  const [platform, setPlatform] = useState<'AWS' | 'AZURE' | 'GCP'>('AWS')
  const [selectedCredential, setSelectedCredential] = useState<string | null>(null)
  const [credentialForm, setCredentialForm] = useState<CreateCredentialPayload>(blankCredentialForm)

  const credentialsQuery = useQuery({
    queryKey: ['credentials'],
    queryFn: fetchCredentials,
  })

  const historyQuery = useQuery({
    queryKey: ['scan-history'],
    queryFn: fetchScanHistory,
    enabled: platform === 'AWS',
  })

  const createCredentialMutation = useMutation({
    mutationFn: createCredential,
    onSuccess: (credential) => {
      credentialsQuery.refetch()
      setSelectedCredential(String(credential.id))
      setCredentialForm(blankCredentialForm)
      notifications.show({ color: 'green', title: 'Credential saved', message: 'AWS credential stored in MySQL.' })
    },
    onError: () => {
      notifications.show({ color: 'red', title: 'Save failed', message: 'Could not store the AWS credential.' })
    },
  })

  const scanMutation = useMutation({
    mutationFn: runScan,
    onSuccess: () => {
      historyQuery.refetch()
      notifications.show({ color: 'green', title: 'Scan saved', message: 'Scan results were stored in MongoDB.' })
    },
    onError: (error: unknown) => {
      console.error(error)
      notifications.show({ color: 'red', title: 'Scan failed', message: 'Check the selected credential and API logs.' })
    },
  })

  const credentials = Array.isArray(credentialsQuery.data) ? credentialsQuery.data : []
  const awsCredentials = credentials.filter((item) => item?.platform === 'AWS')
  const awsCredentialOptions = awsCredentials.map((item) => ({
    value: String(item.id),
    label: `${item.environment} • ${item.access_key_id}${item.region ? ` • ${item.region}` : ''}`,
  }))

  const handleSaveCredential = () => {
    createCredentialMutation.mutate(credentialForm)
  }

  const handleRunScan = () => {
    if (!selectedCredential) {
      notifications.show({ color: 'yellow', title: 'Select a credential', message: 'Choose a saved AWS credential first.' })
      return
    }
    scanMutation.mutate({ platform, credential_id: Number(selectedCredential) })
  }

  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Title order={2}>Run scan</Title>
          <Text size="sm" c="dimmed">
            Select a platform and use credentials stored in MySQL.
          </Text>
        </div>
      </Group>

      <Tabs value={platform} onChange={(value) => setPlatform((value as 'AWS' | 'AZURE' | 'GCP') ?? 'AWS')}>
        <Tabs.List>
          <Tabs.Tab value="AWS">AWS</Tabs.Tab>
          <Tabs.Tab value="AZURE">Azure</Tabs.Tab>
          <Tabs.Tab value="GCP">GCP</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="AWS" pt="md">
          <Stack>
            <Card withBorder shadow="sm">
              <Stack gap="sm">
                <Title order={4}>Saved AWS Credentials</Title>
                <Select
                  label="Credential set"
                  placeholder="Choose a saved AWS credential"
                  data={awsCredentialOptions}
                  value={selectedCredential}
                  onChange={setSelectedCredential}
                />
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    Credentials are encrypted before being stored in MySQL.
                  </Text>
                  <Button leftSection={<IconPlayerPlay size={16} />} loading={scanMutation.isPending} onClick={handleRunScan}>
                    Start AWS scan
                  </Button>
                </Group>
              </Stack>
            </Card>

            <Card withBorder shadow="sm">
              <Stack gap="sm">
                <Title order={4}>Add AWS Credential</Title>
                <Stack gap="sm">
                  <TextInput
                    label="Environment"
                    placeholder="Prod"
                    value={credentialForm.environment}
                    onChange={(event) => {
                      const value = event.currentTarget.value
                      setCredentialForm((current) => ({ ...current, environment: value }))
                    }}
                    required
                  />
                  <TextInput
                    label="Region"
                    placeholder="us-east-1"
                    value={credentialForm.region ?? ''}
                    onChange={(event) => {
                      const value = event.currentTarget.value
                      setCredentialForm((current) => ({ ...current, region: value }))
                    }}
                  />
                  <TextInput
                    label="Access Key ID"
                    value={credentialForm.access_key_id}
                    onChange={(event) => {
                      const value = event.currentTarget.value
                      setCredentialForm((current) => ({ ...current, access_key_id: value }))
                    }}
                    required
                  />
                  <PasswordInput
                    label="Secret Access Key"
                    value={credentialForm.secret_key}
                    onChange={(event) => {
                      const value = event.currentTarget.value
                      setCredentialForm((current) => ({ ...current, secret_key: value }))
                    }}
                    required
                  />
                  <Button type="button" loading={createCredentialMutation.isPending} onClick={handleSaveCredential}>
                    Save AWS credential
                  </Button>
                </Stack>
              </Stack>
            </Card>

            {scanMutation.isError && (
              <Alert color="red" icon={<IconAlertCircle size={16} />}>
                Scan failed. See API logs for the exact AWS error.
              </Alert>
            )}

            {scanMutation.data && (
              <Card withBorder shadow="sm">
                <Stack gap="sm">
                  <Title order={4}>Latest AWS Scan</Title>
                  <Text size="sm" c="dimmed">
                    MongoDB document id: {scanMutation.data.stored_scan_id}
                  </Text>
                  <Card bg="gray.0" padding="sm" radius="md" withBorder>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(scanMutation.data.analysis, null, 2).slice(0, 1200) || 'Empty analysis'}
                    </pre>
                  </Card>
                  <Group gap="sm">
                    <Button component="a" href={scanMutation.data.reports.html} target="_blank" variant="light" leftSection={<IconFileText size={16} />}>
                      HTML report
                    </Button>
                    <Button component="a" href={scanMutation.data.reports.json} target="_blank" variant="default" leftSection={<IconFileText size={16} />}>
                      JSON report
                    </Button>
                  </Group>
                </Stack>
              </Card>
            )}

            <Card withBorder shadow="sm">
              <Stack gap="sm">
                <Title order={4}>Recent AWS Scan History</Title>
                {Array.isArray(historyQuery.data?.results) && historyQuery.data.results.length ? (
                  historyQuery.data.results.map((item) => (
                    <Card key={item.id} bg="gray.0" padding="sm" radius="md" withBorder>
                      <Stack gap={6}>
                        <Group justify="space-between">
                          <Text fw={600}>
                            {item.metadata?.platform ?? 'Unknown'} / {item.metadata?.environment ?? 'Unknown'}
                          </Text>
                          <Badge variant="light">{item.summary?.failed ?? 0} findings</Badge>
                        </Group>
                        <Text size="sm" c="dimmed">
                          {item.metadata?.scan_time ? new Date(item.metadata.scan_time).toLocaleString() : 'Unknown time'}
                        </Text>
                        <Text size="sm">
                          Critical: {item.summary?.severity_counts?.critical ?? 0} | High: {item.summary?.severity_counts?.high ?? 0} |
                          Medium: {item.summary?.severity_counts?.medium ?? 0} | Low: {item.summary?.severity_counts?.low ?? 0}
                        </Text>
                      </Stack>
                    </Card>
                  ))
                ) : (
                  <Text size="sm" c="dimmed">
                    No AWS scan history yet.
                  </Text>
                )}
              </Stack>
            </Card>
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="AZURE" pt="md">
          <Card withBorder shadow="sm">
            <Stack>
              <Title order={4}>Azure</Title>
              <Text c="dimmed">Blank placeholder for now. Azure credential storage and scanning are not implemented yet.</Text>
            </Stack>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="GCP" pt="md">
          <Card withBorder shadow="sm">
            <Stack>
              <Title order={4}>GCP</Title>
              <Text c="dimmed">Blank placeholder for now. GCP credential storage and scanning are not implemented yet.</Text>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}
