import React from 'react'
import styled from 'styled-components'
import { useLocation, Link } from 'react-router-dom'
import { Construction, ArrowLeft, Home, AlertTriangle } from 'lucide-react'

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: ${({ theme }) => theme.spacing['2xl']};
  text-align: center;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    padding: ${({ theme }) => theme.spacing.xl};
  }
`

const IconContainer = styled.div`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: ${({ theme }) => theme.colors.warning.main}15;
  border: 3px solid ${({ theme }) => theme.colors.warning.main}30;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${({ theme }) => theme.spacing.xl};
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    inset: -8px;
    border-radius: 50%;
    border: 2px dashed ${({ theme }) => theme.colors.warning.main}20;
  }
`

const MainIcon = styled.div`
  color: ${({ theme }) => theme.colors.warning.main};
  position: relative;
  z-index: 1;
`

const Title = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes['3xl']};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: ${({ theme }) => theme.spacing.md};
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    font-size: ${({ theme }) => theme.fontSizes['2xl']};
  }
`

const Subtitle = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  color: ${({ theme }) => theme.colors.text.secondary};
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  max-width: 500px;
  line-height: 1.6;
`

const PathInfo = styled.div`
  background: ${({ theme }) => theme.colors.background.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.md};
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.lg};
  margin: ${({ theme }) => theme.spacing.lg} 0;
  font-family: ${({ theme }) => theme.fonts.mono};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text.secondary};
  word-break: break-all;
`

const ButtonGroup = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.md};
  margin-top: ${({ theme }) => theme.spacing.xl};
  flex-wrap: wrap;
  justify-content: center;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}) {
    flex-direction: column;
    width: 100%;
    max-width: 300px;
  }
`

const ActionButton = styled(Link)<{ variant?: 'primary' | 'secondary' }>`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.lg};
  border-radius: ${({ theme }) => theme.radii.md};
  text-decoration: none;
  font-size: ${({ theme }) => theme.fontSizes.base};
  font-weight: 500;
  font-family: ${({ theme }) => theme.fonts.primary};
  transition: all 0.2s ease;
  border: 2px solid;
  
  ${({ theme, variant = 'primary' }) => {
    if (variant === 'primary') {
      return `
        background: ${theme.colors.primary.main};
        color: ${theme.colors.text.inverse};
        border-color: ${theme.colors.primary.main};
        
        &:hover {
          background: ${theme.colors.primary.dark};
          border-color: ${theme.colors.primary.dark};
          text-decoration: none;
          transform: translateY(-1px);
        }
      `
    } else {
      return `
        background: transparent;
        color: ${theme.colors.text.primary};
        border-color: ${theme.colors.border.medium};
        
        &:hover {
          background: ${theme.colors.background.secondary};
          border-color: ${theme.colors.border.dark};
          text-decoration: none;
          transform: translateY(-1px);
        }
      `
    }
  }}
  
  &:active {
    transform: translateY(0);
  }
`

const FeatureInfo = styled.div`
  margin-top: ${({ theme }) => theme.spacing['2xl']};
  padding-top: ${({ theme }) => theme.spacing.xl};
  border-top: 1px solid ${({ theme }) => theme.colors.border.light};
  max-width: 600px;
`

const FeatureTitle = styled.h3`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: ${({ theme }) => theme.spacing.md};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  justify-content: center;
`

const FeatureDescription = styled.p`
  color: ${({ theme }) => theme.colors.text.secondary};
  line-height: 1.6;
  margin-bottom: ${({ theme }) => theme.spacing.md};
`

const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
  display: inline-block;
`

const FeatureItem = styled.li`
  color: ${({ theme }) => theme.colors.text.secondary};
  margin-bottom: ${({ theme }) => theme.spacing.xs};
  position: relative;
  padding-left: ${({ theme }) => theme.spacing.lg};
  
  &::before {
    content: '•';
    color: ${({ theme }) => theme.colors.primary.main};
    position: absolute;
    left: 0;
    font-weight: bold;
  }
`

interface NotImplementedPageProps {
  title?: string
  message?: string
  showPath?: boolean
  features?: string[]
}

const NotImplementedPage: React.FC<NotImplementedPageProps> = ({
  title = "Feature Coming Soon",
  message = "We're working hard to bring you this feature. Check back soon for updates!",
  showPath = true,
  features
}) => {
  const location = useLocation()
  const currentPath = location.pathname

  const getContextualFeatures = (path: string): string[] => {
    if (path.includes('/account') || path.includes('/profile')) {
      return [
        'Profile management and settings',
        'Account security options',
        'Notification preferences',
        'Data export tools'
      ]
    }
    if (path.includes('/transaction')) {
      return [
        'Transaction categorization',
        'Advanced filtering and search',
        'Bulk transaction management',
        'Transaction attachments'
      ]
    }
    if (path.includes('/investment')) {
      return [
        'Portfolio tracking and analysis',
        'Investment performance metrics',
        'Asset allocation recommendations',
        'Market insights and news'
      ]
    }
    if (path.includes('/budget')) {
      return [
        'Smart budgeting tools',
        'Spending category limits',
        'Budget vs actual comparisons',
        'Automated savings goals'
      ]
    }
    if (path.includes('/report') || path.includes('/analytic')) {
      return [
        'Interactive financial reports',
        'Custom dashboard widgets',
        'Trend analysis and forecasting',
        'Export capabilities (PDF, Excel)'
      ]
    }
    return [
      'Advanced financial tracking',
      'Personalized insights and recommendations',
      'Secure bank account integration',
      'Mobile-responsive design'
    ]
  }

  const displayFeatures = features || getContextualFeatures(currentPath)

  return (
    <PageContainer>
      <IconContainer>
        <MainIcon>
          <Construction size={48} />
        </MainIcon>
      </IconContainer>
      
      <Title>{title}</Title>
      <Subtitle>{message}</Subtitle>
      
      {showPath && currentPath !== '/' && (
        <PathInfo>
          Requested path: {currentPath}
        </PathInfo>
      )}
      
      <ButtonGroup>
        <ActionButton to="/" variant="primary">
          <Home size={18} />
          Go Home
        </ActionButton>
        <ActionButton to="javascript:history.back()" variant="secondary" onClick={(e) => {
          e.preventDefault()
          window.history.back()
        }}>
          <ArrowLeft size={18} />
          Go Back
        </ActionButton>
      </ButtonGroup>
      
      {displayFeatures.length > 0 && (
        <FeatureInfo>
          <FeatureTitle>
            <AlertTriangle size={20} />
            What's Coming
          </FeatureTitle>
          <FeatureDescription>
            This feature is part of our roadmap and will include:
          </FeatureDescription>
          <FeatureList>
            {displayFeatures.map((feature, index) => (
              <FeatureItem key={index}>{feature}</FeatureItem>
            ))}
          </FeatureList>
        </FeatureInfo>
      )}
    </PageContainer>
  )
}

export default NotImplementedPage