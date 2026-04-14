import {
  Anchor,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  Paper,
  PasswordInput,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconShieldCheck } from '@tabler/icons-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { resolvedApiBaseUrl } from '../api/client'
import { useAuth } from '../context/AuthContext'

export const LoginPage: React.FC = () => {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(username, password)
      notifications.show({ title: 'Welcome', message: 'Login successful', color: 'green' })
      navigate('/dashboard')
    } catch (err) {
      console.error(err)
      notifications.show({ title: 'Login failed', message: 'Check your credentials', color: 'red' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container fluid className="login-shell">
      <div className="login-glow login-glow-a" />
      <div className="login-glow login-glow-b" />

      <Paper className="login-panel" radius="xl" shadow="xl" withBorder>
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing={0}>
          <Stack className="login-hero" justify="space-between">
            <div>
              <Badge color="cyan" variant="white" size="lg">
                Cloud Security Suite
              </Badge>
              <Title order={1} className="login-title" mt="md">
                Protect every cloud asset before risk becomes incident.
              </Title>
              <Text className="login-subtitle" mt="sm">
                Monitor IAM, S3, and EC2 exposure with continuous scans and beautifully summarized reports.
              </Text>
            </div>

            <Group gap="sm">
              <ThemeIcon radius="xl" size={34} variant="white" color="indigo">
                <IconShieldCheck size={18} />
              </ThemeIcon>
              <Text fw={600}>Trusted admin access only</Text>
            </Group>
          </Stack>

          <Stack className="login-form-wrap" justify="center">
            <Title order={3}>Cloud Audit Login</Title>

            <Text size="sm" c="dimmed">
              Use the credentials configured in the API environment.
            </Text>

            <form onSubmit={handleSubmit}>
              <Stack gap="md">
                <TextInput
                  label="Username"
                  placeholder="admin"
                  size="md"
                  value={username}
                  onChange={(e) => setUsername(e.currentTarget.value)}
                  required
                />
                <PasswordInput
                  label="Password"
                  placeholder="••••••••"
                  size="md"
                  value={password}
                  onChange={(e) => setPassword(e.currentTarget.value)}
                  required
                />
                <Button type="submit" loading={loading} fullWidth size="md" radius="md" className="login-button">
                  Sign in
                </Button>
              </Stack>
            </form>

            <Divider my="xs" />

            <Group justify="space-between" pt={2}>
              <Text size="xs" c="dimmed">
                API base: {resolvedApiBaseUrl}
              </Text>
              <Anchor size="xs" href="https://github.com" target="_blank">
                Docs
              </Anchor>
            </Group>
          </Stack>
        </SimpleGrid>
      </Paper>
    </Container>
  )
}
