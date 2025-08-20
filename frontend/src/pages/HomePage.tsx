import styled from 'styled-components'

const PageContainer = styled.div`
  text-align: center;
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

function HomePage() {
  return (
    <PageContainer>
      <Title>Welcome to AI Financial Assistant</Title>
      <Subtitle>
        Your intelligent companion for managing finances, tracking expenses, and making informed financial decisions.
      </Subtitle>
      
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