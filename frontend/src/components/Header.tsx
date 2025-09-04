import styled from 'styled-components'
import { Link, useNavigate } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import { selectIsAuthenticated, selectCurrentUser, logout } from '../store/slices/authSlice'
import { useLogoutAuthLogoutPostMutation } from '../store/api/generated'

const HeaderContainer = styled.header`
  background-color: ${({ theme }) => theme.colors.background.secondary};
  border-bottom: 1px solid ${({ theme }) => theme.colors.border.light};
  padding: ${({ theme }) => theme.spacing.md} 0;
`

const Nav = styled.nav`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 ${({ theme }) => theme.spacing.lg};
  display: flex;
  justify-content: space-between;
  align-items: center;
`

const Logo = styled(Link)`
  font-size: ${({ theme }) => theme.fontSizes.xl};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary.main};
  text-decoration: none;

  &:hover {
    color: ${({ theme }) => theme.colors.primary.dark};
    text-decoration: none;
  }
`

const NavLinks = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.lg};
`

const NavLink = styled(Link)`
  color: ${({ theme }) => theme.colors.text.secondary};
  font-weight: 500;
  
  &:hover {
    color: ${({ theme }) => theme.colors.primary.main};
  }
`

const AuthSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
`

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  color: ${({ theme }) => theme.colors.text.secondary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
`

const LogoutButton = styled.button`
  background: none;
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  color: ${({ theme }) => theme.colors.text.secondary};
  padding: ${({ theme }) => theme.spacing.xs} ${({ theme }) => theme.spacing.sm};
  border-radius: 4px;
  cursor: pointer;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  transition: all 0.2s ease;
  
  &:hover {
    background: ${({ theme }) => theme.colors.background.secondary};
    border-color: ${({ theme }) => theme.colors.primary.main};
    color: ${({ theme }) => theme.colors.primary.main};
  }
`

const LoginButton = styled(Link)`
  background: ${({ theme }) => theme.colors.primary.main};
  color: white;
  padding: ${({ theme }) => theme.spacing.xs} ${({ theme }) => theme.spacing.md};
  border-radius: 4px;
  text-decoration: none;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${({ theme }) => theme.colors.primary.dark};
    text-decoration: none;
  }
`

function Header() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const currentUser = useSelector(selectCurrentUser)
  const [logoutMutation] = useLogoutAuthLogoutPostMutation()

  const handleLogout = async () => {
    try {
      // Call the logout endpoint
      await logoutMutation().unwrap()
    } catch (error) {
      // Even if the API call fails, we still want to clear local state
      console.warn('Logout API call failed, clearing local state anyway:', error)
    } finally {
      // Clear local auth state
      dispatch(logout())
      // Navigate to home
      navigate('/')
    }
  }

  return (
    <HeaderContainer>
      <Nav>
        <Logo to="/">AI Financial Assistant</Logo>
        <NavLinks>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/about">About</NavLink>
        </NavLinks>
        <AuthSection>
          {isAuthenticated ? (
            <>
              <UserInfo>
                <span>Hello, {currentUser?.name || currentUser?.email}</span>
              </UserInfo>
              <LogoutButton onClick={handleLogout}>
                Logout
              </LogoutButton>
            </>
          ) : (
            <LoginButton to="/login">
              Sign In
            </LoginButton>
          )}
        </AuthSection>
      </Nav>
    </HeaderContainer>
  )
}

export default Header