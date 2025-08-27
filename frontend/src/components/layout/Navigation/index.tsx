import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import { 
  Home, 
  User, 
  Settings, 
  Menu, 
  X,
  LogOut,
  DollarSign,
  TrendingUp,
  PieChart,
  CreditCard,
  Target,
  BarChart3,
  Info
} from 'lucide-react'
import { selectIsAuthenticated, selectCurrentUser, logout } from '../../../store/slices/authSlice'
import { NavigationItem } from '../../../types/navigation'
import {
  NavigationContainer,
  MobileMenuButton,
  MobileOverlay,
  NavigationList,
  NavigationLink,
  NavigationSection,
  NavigationSectionTitle,
  UserSection,
  UserInfo,
  LogoutButton,
  BreadcrumbNav,
  BreadcrumbLink
} from './styles'

interface NavigationSection {
  title: string
  items: NavigationItem[]
}

const getNavigationSections = (isAuthenticated: boolean): NavigationSection[] => [
  {
    title: 'Overview',
    items: [
      {
        id: 'home-dashboard',
        label: isAuthenticated ? 'Dashboard' : 'Home',
        path: '/',
        icon: isAuthenticated ? BarChart3 : Home,
        requiresAuth: false // This item shows for both states
      }
    ]
  },
  {
    title: 'Information',
    items: [
      {
        id: 'about',
        label: 'About',
        path: '/about',
        icon: Info,
        requiresAuth: false
      }
    ]
  },
  {
    title: 'Financial Management',
    items: [
      {
        id: 'accounts',
        label: 'Accounts',
        path: '/accounts',
        icon: CreditCard,
        requiresAuth: true
      },
      {
        id: 'transactions',
        label: 'Transactions',
        path: '/transactions',
        icon: DollarSign,
        requiresAuth: true
      },
      {
        id: 'investments',
        label: 'Investments',
        path: '/investments',
        icon: TrendingUp,
        requiresAuth: true
      },
      {
        id: 'budgets',
        label: 'Budgets',
        path: '/budgets',
        icon: Target,
        requiresAuth: true
      }
    ]
  },
  {
    title: 'Analytics',
    items: [
      {
        id: 'reports',
        label: 'Reports',
        path: '/reports',
        icon: BarChart3,
        requiresAuth: true
      },
      {
        id: 'analytics',
        label: 'Analytics',
        path: '/analytics',
        icon: PieChart,
        requiresAuth: true
      }
    ]
  },
  {
    title: 'Account',
    items: [
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

  // Get navigation sections based on authentication status
  const navigationSections = getNavigationSections(isAuthenticated)
  
  // Filter sections based on authentication requirements
  const visibleSections = navigationSections.map(section => ({
    ...section,
    items: section.items.filter(item => !item.requiresAuth || isAuthenticated)
  })).filter(section => section.items.length > 0)

  // Flatten navigation items for breadcrumb generation
  const allNavigationItems = navigationSections.flatMap(section => section.items)

  // Generate breadcrumbs based on current path
  const generateBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(segment => segment)
    const breadcrumbs = [{ label: 'Home', path: '/' }]
    
    let currentPath = ''
    pathSegments.forEach(segment => {
      currentPath += `/${segment}`
      const matchedItem = allNavigationItems.find(item => item.path === currentPath)
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

        {/* Navigation Links by Section */}
        {visibleSections.map((section) => (
          <NavigationSection key={section.title}>
            <NavigationSectionTitle>{section.title}</NavigationSectionTitle>
            <NavigationList>
              {section.items.map((item) => {
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
                        <Icon size={20} />
                        <span>{item.label}</span>
                      </NavigationLink>
                    </li>
                  )
                })}
              </NavigationList>
            </NavigationSection>
        ))}

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