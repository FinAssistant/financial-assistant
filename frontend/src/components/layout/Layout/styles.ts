import styled from 'styled-components'

export const LayoutContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: ${({ theme }) => theme.colors.background.primary};
`

export const MainContent = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  
  @media (min-width: ${({ theme }) => theme.breakpoints.lg}) {
    flex-direction: column;
    margin-left: 280px; /* Account for sidebar width */
  }
`

export const ContentWrapper = styled.div`
  flex: 1;
  padding: ${({ theme }) => theme.spacing.md};
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  
  @media (min-width: ${({ theme }) => theme.breakpoints.md}) {
    padding: ${({ theme }) => theme.spacing.lg};
  }
  
  @media (min-width: ${({ theme }) => theme.breakpoints.lg}) {
    padding: ${({ theme }) => theme.spacing.xl};
  }
`