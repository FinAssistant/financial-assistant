import styled from 'styled-components'
import { Link } from 'react-router-dom'

const PageContainer = styled.div`
  text-align: center;
  margin: 0 ${({ theme }) => theme.spacing['2xl']};
  padding: ${({ theme }) => theme.spacing['2xl']} 0;
`

const Title = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes['4xl']};
  color: ${({ theme }) => theme.colors.primary.main};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
`

const Subtitle = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  color: ${({ theme }) => theme.colors.text.secondary};
  max-width: 600px;
  margin: 0 auto ${({ theme }) => theme.spacing['2xl']};
  line-height: 1.6;
`

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: ${({ theme }) => theme.spacing.xl};
  margin-top: ${({ theme }) => theme.spacing['2xl']};
`

const FeatureCard = styled.div`
  padding: ${({ theme }) => theme.spacing.xl};
  background-color: ${({ theme }) => theme.colors.background.secondary};
  border-radius: ${({ theme }) => theme.radii.lg};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  text-align: left;
`

const FeatureTitle = styled.h3`
  font-size: ${({ theme }) => theme.fontSizes.xl};
  margin-bottom: ${({ theme }) => theme.spacing.md};
  color: ${({ theme }) => theme.colors.text.primary};
`

const FeatureDescription = styled.p`
  color: ${({ theme }) => theme.colors.text.secondary};
  line-height: 1.6;
`

const CTASection = styled.div`
  margin: ${({ theme }) => theme.spacing['2xl']} 0;
`

const LoginButton = styled(Link)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: ${({ theme }) => theme.colors.primary.main};
  color: ${({ theme }) => theme.colors.text.inverse};
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.xl};
  border-radius: ${({ theme }) => theme.radii.lg};
  text-decoration: none;
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 600;
  font-family: ${({ theme }) => theme.fonts.primary};
  transition: all 0.2s ease;
  box-shadow: ${({ theme }) => theme.shadows.md};
  
  &:hover {
    background: ${({ theme }) => theme.colors.primary.dark};
    text-decoration: none;
    transform: translateY(-2px);
    box-shadow: ${({ theme }) => theme.shadows.lg};
  }
  
  &:active {
    transform: translateY(0);
  }
`

function HomePage() {
  return (
    <PageContainer>
      <Title>Welcome to AI Financial Assistant</Title>
      <Subtitle>
        Your intelligent companion for managing finances, tracking expenses, and making informed financial decisions.
      </Subtitle>

      <CTASection>
        <LoginButton to="/login">
          Get Started - Sign In
        </LoginButton>
      </CTASection>

      <FeatureGrid>
        <FeatureCard>
          <FeatureTitle>Smart Analytics</FeatureTitle>
          <FeatureDescription>
            Get AI-powered insights into your spending patterns and financial habits.
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureTitle>Secure Banking</FeatureTitle>
          <FeatureDescription>
            Connect your bank accounts securely and view all your finances in one place.
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureTitle>Personalized Advice</FeatureTitle>
          <FeatureDescription>
            Receive tailored financial recommendations based on your goals and situation.
          </FeatureDescription>
        </FeatureCard>
      </FeatureGrid>
    </PageContainer>
  )
}

export default HomePage