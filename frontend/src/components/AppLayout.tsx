import { AppShell, Burger, Button, Group, NavLink, ScrollArea, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconFileTypePdf, IconLogout, IconReportAnalytics, IconServer, IconShield, IconUsers } from '@tabler/icons-react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: IconShield },
  { label: 'Scan', to: '/scan', icon: IconReportAnalytics },
  { label: 'Reports', to: '/reports', icon: IconFileTypePdf },
  { label: 'Resources', to: '/resources', icon: IconServer },
]

export const AppLayout: React.FC = () => {
  const [opened, { toggle }] = useDisclosure()
  const { user, logout } = useAuth()
  const location = useLocation()
  const items = user?.role === 'admin' ? [...navItems, { label: 'Admin', to: '/admin/users', icon: IconUsers }] : navItems

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header px="md">
        <Group h="100%" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Title order={4}>Cloud Audit Dashboard</Title>
          </Group>
          <Group gap="xs">
            <IconUsers size={18} />
            <Text size="sm">{user?.username}</Text>
            <Button variant="light" size="xs" leftSection={<IconLogout size={16} />} onClick={logout}>
              Logout
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="sm">
        <AppShell.Section grow component={ScrollArea}>
          {items.map((item) => (
            <NavLink
              key={item.to}
              component={Link}
              to={item.to}
              label={item.label}
              leftSection={<item.icon size={18} />}
              active={location.pathname === item.to}
            />
          ))}
        </AppShell.Section>
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  )
}
