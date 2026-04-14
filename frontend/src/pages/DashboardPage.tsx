import { Alert, Button, Card, Grid, Group, Skeleton, Stack, Text, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useQuery } from '@tanstack/react-query'
import { IconAlertCircle, IconPlayerPlay, IconReport } from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import { fetchScanSummary } from '../api/scan'

export const DashboardPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery({ queryKey: ['scan-summary'], queryFn: fetchScanSummary })
  const hasAnalysis = Boolean(data?.analysis)

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Dashboard</Title>
        <Button
          component={Link}
          to="/scan"
          leftSection={<IconPlayerPlay size={16} />}
          onClick={() => notifications.clean()}
        >
          Run a scan
        </Button>
      </Group>

      <Grid>
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card withBorder shadow="sm">
            <Stack gap="sm">
              <Group gap="xs">
                <IconReport size={18} />
                <Title order={4}>Latest analysis</Title>
              </Group>
              {isLoading && <Skeleton height={100} radius="md" />}
              {isError && (
                <Alert color="blue" icon={<IconAlertCircle size={16} />}>
                  No scans available.
                </Alert>
              )}
              {!isLoading && !isError && !hasAnalysis && (
                <Alert color="blue" icon={<IconAlertCircle size={16} />}>No scans available.</Alert>
              )}
              {!isLoading && !isError && hasAnalysis && (
                <Text size="sm" c="dimmed">
                  Analysis JSON preview:
                </Text>
              )}
              {!isLoading && !isError && hasAnalysis && (
                <Card bg="gray.0" padding="sm" radius="md" withBorder>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(data.analysis, null, 2).slice(0, 800) || 'Empty analysis'}
                  </pre>
                </Card>
              )}
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
