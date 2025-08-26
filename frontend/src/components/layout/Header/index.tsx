import React from 'react'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated } from '../../../store/slices/authSlice'
import { 
  HeaderContainer, 
  Nav, 
  Logo, 
  NavLinks, 
  NavLink,
  AuthSection,
  LoginButton 
} from './styles'

const Header: React.FC = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated)

  return (
    <HeaderContainer>
      <Nav>
        <Logo to="/">AI Financial Assistant</Logo>
        <NavLinks>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/about">About</NavLink>
        </NavLinks>
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