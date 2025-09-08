import React from 'react'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated } from '../../../store/slices/authSlice'
import Header from '../Header'
import Navigation from '../Navigation'
import {
  LayoutContainer,
  MainContent,
  ContentWrapper
} from './styles'

interface LayoutProps {
  children: React.ReactNode
  showNavigation?: boolean
  loading?: boolean
  error?: string | null
}

const Layout: React.FC<LayoutProps> = ({
  children,
  showNavigation = true,
  loading = false,
  error = null
}) => {
  const isAuthenticated = useSelector(selectIsAuthenticated)

  return (
    <LayoutContainer>
      <Header />
      {showNavigation && isAuthenticated && <Navigation />}
      <MainContent>
        <ContentWrapper>
          {error ? (
            <div role="alert">Error: {error}</div>
          ) : loading ? (
            <div>Loading...</div>
          ) : (
            children
          )}
        </ContentWrapper>
      </MainContent>
    </LayoutContainer>
  )
}

export default Layout