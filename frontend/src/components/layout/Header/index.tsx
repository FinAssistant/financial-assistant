import React from 'react'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated } from '../../../store/slices/authSlice'
import { 
  HeaderContainer, 
  Nav, 
  Logo, 
  AuthSection,
  LoginButton 
} from './styles'

const Header: React.FC = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated)

  return (
    <HeaderContainer>
      <Nav>
        <Logo to="/">AI Financial Assistant</Logo>
        <AuthSection>
          {!isAuthenticated && (
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