import {
  Badge,
  Button,
  Card,
  Center,
  Group,
  RingProgress,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { IconDownload, IconFileTypePdf } from '@tabler/icons-react'
import { useMemo, useState } from 'react'
import { buildPdfReportUrl } from '../api/reports'
import { fetchScanHistory } from '../api/scan'

const formatDate = (value?: string | null) => (value ? new Date(value).toLocaleString() : 'Unknown time')

export const ReportsPage: React.FC = () => {
  const history = useQuery({ queryKey: ['scan-history'], queryFn: fetchScanHistory })
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null)

  const scans = history.data?.results ?? []
  const options = useMemo(
    () =>
      scans.map((scan) => ({
        value: scan.id,
        label: `${scan.metadata.platform} / ${scan.metadata.environment} • ${formatDate(scan.metadata.scan_time)}`,
      })),
    [scans],
  )

  const selectedScan = useMemo(
    () => scans.find((scan) => scan.id === selectedScanId) ?? scans[0],
    [scans, selectedScanId],
  )

  const severity = selectedScan?.summary?.severity_counts
  const downloadUrl = selectedScan ? buildPdfReportUrl(selectedScan.id) : '#'
  const totalFindings = selectedScan?.summary?.failed ?? 0

  return (
    <Stack gap="lg">
      <Card
        radius="lg"
        p="lg"
        withBorder
        style={{
          background: 'linear-gradient(125deg, #0ea5e9 0%, #2563eb 55%, #1d4ed8 100%)',
          color: 'white',
        }}
      >
        <Group justify="space-between" align="center">
          <Stack gap={2}>
            <Title order={2} c="white">
              Reports Center
            </Title>
            <Text c="rgba(255,255,255,0.88)">Download polished PDF reports from your recent scans.</Text>
          </Stack>
          <IconFileTypePdf size={44} />
        </Group>
      </Card>

      <Card radius="md" withBorder>
        <Stack>
          <Group justify="space-between" align="end">
            <Select
              label="Recent scan"
              placeholder={history.isLoading ? 'Loading recent scans...' : 'Select a scan'}
              value={selectedScan?.id ?? null}
              onChange={setSelectedScanId}
              data={options}
              searchable
              style={{ flex: 1 }}
              disabled={history.isLoading || options.length === 0}
            />
            <Button
              component="a"
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              leftSection={<IconDownload size={16} />}
              disabled={!selectedScan}
              style={{ backgroundColor: '#ef4444' }}
            >
              Download PDF
            </Button>
          </Group>
          {!history.isLoading && !selectedScan && (
            <Text size="sm" c="dimmed">
              No scans found yet. Run a scan first, then download its report.
            </Text>
          )}
        </Stack>
      </Card>

      {selectedScan && (
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
          <Card withBorder radius="md">
            <Stack>
              <Group justify="space-between">
                <Text fw={700}>Selected Scan</Text>
                <Badge color="blue" variant="light">
                  {selectedScan.metadata.platform}
                </Badge>
              </Group>
              <Text>
                Environment: <b>{selectedScan.metadata.environment}</b>
              </Text>
              <Text c="dimmed">Scanned at: {formatDate(selectedScan.metadata.scan_time)}</Text>
              <Text>
                Findings: <b>{totalFindings}</b>
              </Text>
            </Stack>
          </Card>

          <Card withBorder radius="md">
            <Stack align="center" justify="center" h="100%">
              <RingProgress
                size={170}
                thickness={18}
                roundCaps
                sections={[
                  { value: (severity?.critical ?? 0) * 4, color: '#ef4444' },
                  { value: (severity?.high ?? 0) * 3, color: '#f97316' },
                  { value: (severity?.medium ?? 0) * 2, color: '#eab308' },
                  { value: severity?.low ?? 0, color: '#22c55e' },
                ]}
                label={
                  <Center>
                    <Stack gap={0} align="center">
                      <Text size="xs" c="dimmed">
                        Findings
                      </Text>
                      <Text fw={700}>{totalFindings}</Text>
                    </Stack>
                  </Center>
                }
              />
              <Group gap="xs">
                <Badge color="red">C {severity?.critical ?? 0}</Badge>
                <Badge color="orange">H {severity?.high ?? 0}</Badge>
                <Badge color="yellow" c="black">
                  M {severity?.medium ?? 0}
                </Badge>
                <Badge color="green">L {severity?.low ?? 0}</Badge>
              </Group>
            </Stack>
          </Card>
        </SimpleGrid>
      )}
    </Stack>
  )
}
