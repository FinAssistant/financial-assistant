import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated, selectIsLoading } from '../../../store/slices/authSlice'
import { LoadingContainer, LoadingSpinner, LoadingText } from './styles'

interface AuthGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
}

const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  requireAuth = true, 
  redirectTo = '/login' 
}) => {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isLoading = useSelector(selectIsLoading)
  const location = useLocation()

  // Show loading spinner while checking authentication status
  if (isLoading) {
    return (
      <LoadingContainer>
        <LoadingSpinner />
        <LoadingText>Loading...</LoadingText>
      </LoadingContainer>
    )
  }

  // If authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    // Save the attempted location for redirecting after login
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  // If user is authenticated but tries to access auth pages (login/register)
  if (!requireAuth && isAuthenticated) {
    // Redirect to the page they were trying to access, or home
    const from = location.state?.from?.pathname || '/'
    return <Navigate to={from} replace />
  }

  // Render children if all checks pass
  return <>{children}</>
}

export default AuthGuard