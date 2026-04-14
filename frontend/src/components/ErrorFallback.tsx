import { Alert, Button, Container, Group, Stack, Text, Title } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'

type ErrorFallbackProps = {
  error: Error
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error }) => {
  return (
    <Container size="sm" py="xl">
      <Stack gap="md">
        <Title order={3}>Something went wrong</Title>
        <Alert color="red" icon={<IconAlertCircle size={16} />}>
          <Text size="sm">The page hit an unexpected error and could not render.</Text>
          <Text size="xs" c="dimmed" mt="xs">
            {error.message || 'Unknown client error'}
          </Text>
        </Alert>
        <Group>
          <Button onClick={() => window.location.reload()}>Reload page</Button>
        </Group>
      </Stack>
    </Container>
  )
}
