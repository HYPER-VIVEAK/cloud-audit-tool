import { Navigate, Outlet } from 'react-router-dom'
import { Center, Loader } from '@mantine/core'
import { useAuth } from '../context/AuthContext'

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) {
    return (
      <Center mih="100vh">
        <Loader />
      </Center>
    )
  }
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}
