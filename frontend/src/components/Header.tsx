import styled from 'styled-components'
import { Link } from 'react-router-dom'

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

function Header() {
  return (
    <HeaderContainer>
      <Nav>
        <Logo to="/">AI Financial Assistant</Logo>
        <NavLinks>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/about">About</NavLink>
        </NavLinks>
      </Nav>
    </HeaderContainer>
  )
}

export default Header