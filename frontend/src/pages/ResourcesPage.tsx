import { Alert, Card, Group, Select, Skeleton, Stack, Table, Tabs, Text, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { IconCloud, IconServer, IconUsers } from '@tabler/icons-react'
import { useEffect, useMemo, useState } from 'react'
import { listBuckets, listInstances, listUsers } from '../api/resources'
import { fetchScanHistory } from '../api/scan'

const formatDate = (value?: string) => (value ? new Date(value).toLocaleString() : '—')

export const ResourcesPage: React.FC = () => {
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null)

  const history = useQuery({ queryKey: ['scan-history'], queryFn: fetchScanHistory })

  const scanOptions = useMemo(
    () =>
      (history.data?.results ?? []).map((item) => ({
        value: item.id,
        label: `${item.metadata.platform} / ${item.metadata.environment} - ${formatDate(item.metadata.scan_time ?? undefined)}`,
      })),
    [history.data?.results],
  )

  useEffect(() => {
    if (!selectedScanId && scanOptions.length) {
      setSelectedScanId(scanOptions[0].value)
    }
  }, [scanOptions, selectedScanId])

  const users = useQuery({
    queryKey: ['iam-users', selectedScanId],
    queryFn: () => listUsers(selectedScanId),
    enabled: Boolean(selectedScanId),
  })
  const buckets = useQuery({
    queryKey: ['s3-buckets', selectedScanId],
    queryFn: () => listBuckets(selectedScanId),
    enabled: Boolean(selectedScanId),
  })
  const instances = useQuery({
    queryKey: ['ec2-instances', selectedScanId],
    queryFn: () => listInstances(selectedScanId),
    enabled: Boolean(selectedScanId),
  })

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Resources</Title>
        <Text size="sm" c="dimmed">
          IAM, S3, EC2 snapshots
        </Text>
      </Group>

      <Card withBorder>
        <Stack gap="sm">
          <Select
            label="Recent scan"
            placeholder={history.isLoading ? 'Loading scans...' : 'Select a recent scan'}
            data={scanOptions}
            value={selectedScanId}
            onChange={setSelectedScanId}
            searchable
            disabled={history.isLoading || !scanOptions.length}
          />
          {!history.isLoading && !scanOptions.length && (
            <Text size="sm" c="dimmed">
              No scan history found. Run a scan first to load resources for that scan.
            </Text>
          )}
        </Stack>
      </Card>

      {(users.isError || buckets.isError || instances.isError) && (
        <Alert color="red" title="Could not load scoped resources">
          The selected scan may be old and missing credential metadata. Run a new scan and select it.
        </Alert>
      )}

      <Tabs defaultValue="iam">
        <Tabs.List>
          <Tabs.Tab value="iam" leftSection={<IconUsers size={16} />}>IAM Users</Tabs.Tab>
          <Tabs.Tab value="s3" leftSection={<IconCloud size={16} />}>S3 Buckets</Tabs.Tab>
          <Tabs.Tab value="ec2" leftSection={<IconServer size={16} />}>EC2 Instances</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="iam" pt="md">
          <Card withBorder>
            {(users.isLoading || !selectedScanId) && <Skeleton height={120} radius="md" />}
            {selectedScanId && !users.isLoading && (
              <Table striped highlightOnHover withTableBorder withColumnBorders>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>ARN</Table.Th>
                    <Table.Th>Created</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {users.data?.users?.map((u) => (
                    <Table.Tr key={u.arn ?? u.user_name}>
                      <Table.Td>{u.user_name}</Table.Td>
                      <Table.Td>{u.arn}</Table.Td>
                      <Table.Td>{formatDate(u.created)}</Table.Td>
                    </Table.Tr>
                  ))}
                  {!users.data?.users?.length && (
                    <Table.Tr>
                      <Table.Td colSpan={3}>
                        <Text size="sm" c="dimmed">
                          No users found
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="s3" pt="md">
          <Card withBorder>
            {(buckets.isLoading || !selectedScanId) && <Skeleton height={120} radius="md" />}
            {selectedScanId && !buckets.isLoading && (
              <Table striped highlightOnHover withTableBorder withColumnBorders>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Created</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {buckets.data?.buckets?.map((b) => (
                    <Table.Tr key={b.name}>
                      <Table.Td>{b.name}</Table.Td>
                      <Table.Td>{formatDate(b.created)}</Table.Td>
                    </Table.Tr>
                  ))}
                  {!buckets.data?.buckets?.length && (
                    <Table.Tr>
                      <Table.Td colSpan={2}>
                        <Text size="sm" c="dimmed">
                          No buckets found
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="ec2" pt="md">
          <Card withBorder>
            {(instances.isLoading || !selectedScanId) && <Skeleton height={120} radius="md" />}
            {selectedScanId && !instances.isLoading && (
              <Table striped highlightOnHover withTableBorder withColumnBorders>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>ID</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>State</Table.Th>
                    <Table.Th>Public IP</Table.Th>
                    <Table.Th>Private IP</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {instances.data?.instances?.map((i) => (
                    <Table.Tr key={i.instance_id}>
                      <Table.Td>{i.instance_id}</Table.Td>
                      <Table.Td>{i.type}</Table.Td>
                      <Table.Td>{i.state}</Table.Td>
                      <Table.Td>{i.public_ip ?? '—'}</Table.Td>
                      <Table.Td>{i.private_ip ?? '—'}</Table.Td>
                    </Table.Tr>
                  ))}
                  {!instances.data?.instances?.length && (
                    <Table.Tr>
                      <Table.Td colSpan={5}>
                        <Text size="sm" c="dimmed">
                          No instances found
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}
