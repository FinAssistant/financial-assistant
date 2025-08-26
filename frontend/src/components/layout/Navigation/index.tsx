import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import { 
  Home, 
  User, 
  Settings, 
  Menu, 
  X,
  LogOut 
} from 'lucide-react'
import { selectIsAuthenticated, selectCurrentUser, logout } from '../../../store/slices/authSlice'
import { NavigationItem } from '../../../types/navigation'
import {
  NavigationContainer,
  MobileMenuButton,
  MobileOverlay,
  NavigationList,
  NavigationLink,
  UserSection,
  UserInfo,
  LogoutButton,
  BreadcrumbNav,
  BreadcrumbLink
} from './styles'

const navigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/',
    icon: Home,
    requiresAuth: true
  },
  {
    id: 'profile',
    label: 'Profile',
    path: '/profile',
    icon: User,
    requiresAuth: true
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: Settings,
    requiresAuth: true
  }
]

const Navigation: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()
  const dispatch = useDispatch()
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const currentUser = useSelector(selectCurrentUser)

  const handleLogout = async () => {
    try {
      // Simple logout - just clear local state for now
      dispatch(logout())
      setIsMobileMenuOpen(false)
    } catch (error) {
      console.warn('Logout failed:', error)
      // Still clear local state
      dispatch(logout())
      setIsMobileMenuOpen(false)
    }
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false)
  }

  if (!isAuthenticated) {
    return null
  }

  const visibleItems = navigationItems.filter(item => !item.requiresAuth || isAuthenticated)

  // Generate breadcrumbs based on current path
  const generateBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(segment => segment)
    const breadcrumbs = [{ label: 'Home', path: '/' }]
    
    let currentPath = ''
    pathSegments.forEach(segment => {
      currentPath += `/${segment}`
      const matchedItem = navigationItems.find(item => item.path === currentPath)
      if (matchedItem) {
        breadcrumbs.push({ label: matchedItem.label, path: currentPath })
      }
    })
    
    return breadcrumbs.length > 1 ? breadcrumbs : []
  }

  const breadcrumbs = generateBreadcrumbs()

  return (
    <>
      {/* Mobile Menu Button */}
      <MobileMenuButton onClick={toggleMobileMenu} aria-label="Toggle navigation">
        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
      </MobileMenuButton>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && <MobileOverlay onClick={closeMobileMenu} />}

      <NavigationContainer $isOpen={isMobileMenuOpen}>
        {/* User Section */}
        {currentUser && (
          <UserSection>
            <UserInfo>
              <User size={16} />
              <span>{currentUser.name || currentUser.email}</span>
            </UserInfo>
            <LogoutButton onClick={handleLogout} title="Logout">
              <LogOut size={16} />
            </LogoutButton>
          </UserSection>
        )}

        {/* Navigation Links */}
        <NavigationList>
          {visibleItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <li key={item.id}>
                <NavigationLink
                  as={Link}
                  to={item.path}
                  $isActive={isActive}
                  onClick={closeMobileMenu}
                >
                  <Icon size={24} />
                  <span>{item.label}</span>
                </NavigationLink>
              </li>
            )
          })}
        </NavigationList>

        {/* Breadcrumb Navigation */}
        {breadcrumbs.length > 0 && (
          <BreadcrumbNav>
            {breadcrumbs.map((breadcrumb, index) => (
              <span key={breadcrumb.path}>
                {index === breadcrumbs.length - 1 ? (
                  <span>{breadcrumb.label}</span>
                ) : (
                  <>
                    <BreadcrumbLink as={Link} to={breadcrumb.path}>
                      {breadcrumb.label}
                    </BreadcrumbLink>
                    <span> / </span>
                  </>
                )}
              </span>
            ))}
          </BreadcrumbNav>
        )}
      </NavigationContainer>
    </>
  )
}

export default Navigation