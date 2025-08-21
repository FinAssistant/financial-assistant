import styled from 'styled-components'

const FooterContainer = styled.footer`
  background-color: ${({ theme }) => theme.colors.background.secondary};
  border-top: 1px solid ${({ theme }) => theme.colors.border.light};
  padding: ${({ theme }) => theme.spacing.lg} 0;
  margin-top: auto;
`

const FooterContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 ${({ theme }) => theme.spacing.lg};
  text-align: center;
  color: ${({ theme }) => theme.colors.text.secondary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
`

function Footer() {
  return (
    <FooterContainer>
      <FooterContent>
        © 2024 AI Financial Assistant. Built with React, TypeScript, and FastAPI.
      </FooterContent>
    </FooterContainer>
  )
}

export default Footer