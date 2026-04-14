import {
  Badge,
  Button,
  Card,
  Group,
  PasswordInput,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { createUser, fetchUsers } from '../api/auth'
import type { CreateUserPayload, UserSummary } from '../api/types'
import { useAuth } from '../context/AuthContext'

const emptyForm: CreateUserPayload = {
  username: '',
  password: '',
  role: 'user',
}

export const AdminUsersPage: React.FC = () => {
  const { user } = useAuth()
  const [users, setUsers] = useState<UserSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<CreateUserPayload>(emptyForm)

  useEffect(() => {
    if (user?.role !== 'admin') {
      return
    }

    fetchUsers()
      .then(setUsers)
      .catch((error) => {
        console.error(error)
        notifications.show({ title: 'Could not load users', message: 'Please try again.', color: 'red' })
      })
      .finally(() => setLoading(false))
  }, [user?.role])

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  const handleCreateUser = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    try {
      const createdUser = await createUser(form)
      setUsers((current) => [createdUser, ...current])
      setForm(emptyForm)
      notifications.show({ title: 'User created', message: `${createdUser.username} is ready to sign in.`, color: 'green' })
    } catch (error) {
      console.error(error)
      notifications.show({ title: 'Create failed', message: 'Check the username and try again.', color: 'red' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="end">
        <div>
          <Title order={2}>Admin User Management</Title>
          <Text c="dimmed">Create application users and review their access roles.</Text>
        </div>
        <Badge color="red" variant="light">
          Admin only
        </Badge>
      </Group>

      <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
        <Card withBorder radius="md" padding="lg">
          <Stack gap="sm">
            <Title order={4}>Add User</Title>
            <Text size="sm" c="dimmed">
              New users will be stored in MySQL with a bcrypt-hashed password.
            </Text>
            <form onSubmit={handleCreateUser}>
              <Stack gap="sm">
                <TextInput
                  label="Username"
                  placeholder="jane.doe"
                  value={form.username}
                     onChange={(event) => {
                       const value = event.currentTarget.value
                       setForm((current) => ({ ...current, username: value }))
                     }}
                  required
                />
                <PasswordInput
                  label="Temporary Password"
                  placeholder="At least 6 characters"
                  value={form.password}
                     onChange={(event) => {
                       const value = event.currentTarget.value
                       setForm((current) => ({ ...current, password: value }))
                     }}
                  required
                />
                <Select
                  label="Role"
                  data={[
                    { value: 'user', label: 'User' },
                    { value: 'admin', label: 'Admin' },
                  ]}
                  value={form.role}
                  onChange={(value) => setForm((current) => ({ ...current, role: (value as 'admin' | 'user') || 'user' }))}
                  allowDeselect={false}
                />
                <Button type="submit" loading={saving}>
                  Create User
                </Button>
              </Stack>
            </form>
          </Stack>
        </Card>

        <Card withBorder radius="md" padding="lg">
          <Stack gap="sm">
            <Title order={4}>Existing Users</Title>
            <Text size="sm" c="dimmed">
              {loading ? 'Loading current users...' : `${users.length} user account(s) found.`}
            </Text>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Username</Table.Th>
                  <Table.Th>Role</Table.Th>
                  <Table.Th>Created</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {users.map((entry) => (
                  <Table.Tr key={entry.id}>
                    <Table.Td>{entry.username}</Table.Td>
                    <Table.Td>
                      <Badge variant="light" color={entry.role === 'admin' ? 'red' : 'blue'}>
                        {entry.role}
                      </Badge>
                    </Table.Td>
                    <Table.Td>{entry.created_at ? new Date(entry.created_at).toLocaleString() : '-'}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Stack>
        </Card>
      </SimpleGrid>
    </Stack>
  )
}
