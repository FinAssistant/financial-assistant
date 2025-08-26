import styled from 'styled-components'

interface NavigationContainerProps {
  $isOpen: boolean
}

interface NavigationLinkProps {
  $isActive: boolean
}

export const MobileMenuButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  top: ${({ theme }) => theme.spacing.md};
  right: ${({ theme }) => theme.spacing.md};
  z-index: 1001;
  background: ${({ theme }) => theme.colors.primary.main};
  color: ${({ theme }) => theme.colors.text.inverse};
  border: none;
  border-radius: ${({ theme }) => theme.radii.md};
  padding: ${({ theme }) => theme.spacing.sm};
  cursor: pointer;
  box-shadow: ${({ theme }) => theme.shadows.md};
  
  @media (min-width: ${({ theme }) => theme.breakpoints.lg}) {
    display: none;
  }
  
  &:hover {
    background: ${({ theme }) => theme.colors.primary.dark};
  }
`

export const MobileOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  
  @media (min-width: ${({ theme }) => theme.breakpoints.lg}) {
    display: none;
  }
`

export const NavigationContainer = styled.nav<NavigationContainerProps>`
  background: ${({ theme }) => theme.colors.background.secondary};
  border-right: 1px solid ${({ theme }) => theme.colors.border.light};
  padding: ${({ theme }) => theme.spacing.md};
  overflow-y: auto;
  
  /* Mobile styles */
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 280px;
  z-index: 1000;
  transform: ${({ $isOpen }) => $isOpen ? 'translateX(0)' : 'translateX(-100%)'};
  transition: transform 0.3s ease-in-out;
  
  @media (min-width: ${({ theme }) => theme.breakpoints.md}) {
    width: 320px;
  }
  
  /* Desktop styles */
  @media (min-width: ${({ theme }) => theme.breakpoints.lg}) {
    position: static;
    transform: none;
    width: 280px;
    height: auto;
    min-height: calc(100vh - 80px); /* Adjust for header height */
    transition: none;
  }
`

export const UserSection = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${({ theme }) => theme.spacing.md};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  background: ${({ theme }) => theme.colors.background.primary};
  border-radius: ${({ theme }) => theme.radii.md};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
`

export const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  color: ${({ theme }) => theme.colors.text.secondary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
`

export const LogoutButton = styled.button`
  display: flex;
  align-items: center;
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.text.secondary};
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing.xs};
  border-radius: ${({ theme }) => theme.radii.sm};
  transition: all 0.2s ease;
  
  &:hover {
    background: ${({ theme }) => theme.colors.background.secondary};
    color: ${({ theme }) => theme.colors.error};
  }
`

export const NavigationList = styled.ul`
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.xs};
`

export const NavigationLink = styled.a<NavigationLinkProps>`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
  padding: ${({ theme }) => theme.spacing.md};
  color: ${({ theme, $isActive }) => 
    $isActive ? theme.colors.primary.main : theme.colors.text.secondary};
  text-decoration: none;
  border-radius: ${({ theme }) => theme.radii.md};
  transition: all 0.2s ease;
  font-weight: 500;
  background: ${({ theme, $isActive }) => 
    $isActive ? theme.colors.primary.main + '10' : 'transparent'};
  border: 1px solid ${({ theme, $isActive }) => 
    $isActive ? theme.colors.primary.main + '20' : 'transparent'};
  
  &:hover {
    background: ${({ theme }) => theme.colors.background.primary};
    color: ${({ theme }) => theme.colors.primary.main};
    border-color: ${({ theme }) => theme.colors.border.medium};
    text-decoration: none;
  }
  
  span {
    font-size: ${({ theme }) => theme.fontSizes.base};
  }
`

export const BreadcrumbNav = styled.div`
  margin-top: ${({ theme }) => theme.spacing.xl};
  padding-top: ${({ theme }) => theme.spacing.md};
  border-top: 1px solid ${({ theme }) => theme.colors.border.light};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text.secondary};
  
  @media (max-width: ${({ theme }) => theme.breakpoints.lg}) {
    display: none;
  }
`

export const BreadcrumbLink = styled.a`
  color: ${({ theme }) => theme.colors.primary.main};
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
`