import React from 'react'
import styled from 'styled-components'
import { TrendingUp, DollarSign, CreditCard, Target, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { ChatInterface } from '../components/chat/ChatInterface'

// Layout components
const DashboardContainer = styled.div`
  padding: ${({ theme }) => theme.spacing.xl};
  max-width: 1200px;
  margin: 0 auto;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    padding: ${({ theme }) => theme.spacing.md};
  }
`

const DashboardHeader = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing['2xl']};
`

const DashboardTitle = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes['3xl']};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    font-size: ${({ theme }) => theme.fontSizes['2xl']};
  }
`

const DashboardSubtitle = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  color: ${({ theme }) => theme.colors.text.secondary};
`

// Stats cards
const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: ${({ theme }) => theme.spacing.xl};
  margin-bottom: ${({ theme }) => theme.spacing['2xl']};
`

const StatCard = styled.div<{ trend?: 'up' | 'down' }>`
  background: ${({ theme }) => theme.colors.background.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: ${({ theme }) => theme.spacing.xl};
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: ${({ theme, trend }) => 
      trend === 'up' ? theme.colors.profit.main : 
      trend === 'down' ? theme.colors.loss.main : 
      theme.colors.primary.main};
  }
`

const StatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${({ theme }) => theme.spacing.md};
`

const StatLabel = styled.h3`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text.secondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
`

const StatIcon = styled.div<{ variant: 'primary' | 'profit' | 'loss' | 'warning' }>`
  width: 40px;
  height: 40px;
  border-radius: ${({ theme }) => theme.radii.md};
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${({ theme, variant }) => {
    switch (variant) {
      case 'profit': return theme.colors.profit.main + '20'
      case 'loss': return theme.colors.loss.main + '20'
      case 'warning': return theme.colors.warning.main + '20'
      default: return theme.colors.primary.main + '20'
    }
  }};
  color: ${({ theme, variant }) => {
    switch (variant) {
      case 'profit': return theme.colors.profit.main
      case 'loss': return theme.colors.loss.main
      case 'warning': return theme.colors.warning.main
      default: return theme.colors.primary.main
    }
  }};
`

const StatValue = styled.div`
  font-size: ${({ theme }) => theme.fontSizes['2xl']};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: ${({ theme }) => theme.spacing.xs};
  font-family: ${({ theme }) => theme.fonts.mono};
`

const StatTrend = styled.div<{ trend: 'up' | 'down' }>`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.xs};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  color: ${({ theme, trend }) => 
    trend === 'up' ? theme.colors.profit.main : theme.colors.loss.main};
`

// Chart containers
const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: ${({ theme }) => theme.spacing.xl};
  margin-bottom: ${({ theme }) => theme.spacing['2xl']};
  
  @media (max-width: ${({ theme }) => theme.breakpoints.lg}) {
    grid-template-columns: 1fr;
  }
`

const ChartCard = styled.div`
  background: ${({ theme }) => theme.colors.background.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: ${({ theme }) => theme.spacing.xl};
`

const ChartTitle = styled.h3`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
`

// Placeholder chart components
const PlaceholderChart = styled.div<{ height: string }>`
  height: ${({ height }) => height};
  background: linear-gradient(135deg, 
    ${({ theme }) => theme.colors.primary.main}10 0%, 
    ${({ theme }) => theme.colors.primary.main}05 100%);
  border-radius: ${({ theme }) => theme.radii.md};
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${({ theme }) => theme.colors.text.secondary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  border: 2px dashed ${({ theme }) => theme.colors.border.medium};
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      45deg,
      transparent,
      transparent 10px,
      ${({ theme }) => theme.colors.primary.main}05 10px,
      ${({ theme }) => theme.colors.primary.main}05 20px
    );
  }
`

const PlaceholderContent = styled.div`
  text-align: center;
  z-index: 1;
  position: relative;
`

const DashboardChatInterface = styled(ChatInterface)`
  /* Dashboard integration styling with proper spacing */
  margin-bottom: ${({ theme }) => theme.spacing['2xl']};
  
  /* Override height for dashboard integration */
  height: 400px;
  max-height: 400px;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    height: 350px;
    max-height: 350px;
  }
`

// Recent activity section
const ActivitySection = styled.div`
  background: ${({ theme }) => theme.colors.background.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: ${({ theme }) => theme.spacing.xl};
`

const ActivityList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
`

const ActivityItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${({ theme }) => theme.spacing.md};
  background: ${({ theme }) => theme.colors.background.primary};
  border-radius: ${({ theme }) => theme.radii.md};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
`

const ActivityInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
`

const ActivityDetails = styled.div``

const ActivityTitle = styled.div`
  font-weight: 500;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: ${({ theme }) => theme.spacing.xs};
`

const ActivityMeta = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text.secondary};
`

const ActivityAmount = styled.div<{ type: 'income' | 'expense' }>`
  font-weight: 600;
  font-family: ${({ theme }) => theme.fonts.mono};
  color: ${({ theme, type }) => 
    type === 'income' ? theme.colors.profit.main : theme.colors.loss.main};
`

const DashboardPage: React.FC = () => {
  return (
    <DashboardContainer>
      <DashboardHeader>
        <DashboardTitle>Financial Dashboard</DashboardTitle>
        <DashboardSubtitle>Overview of your financial health and recent activity</DashboardSubtitle>
      </DashboardHeader>

      {/* Stats Cards */}
      <StatsGrid>
        <StatCard trend="up">
          <StatHeader>
            <StatLabel>Total Balance</StatLabel>
            <StatIcon variant="primary">
              <DollarSign size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>$12,845.67</StatValue>
          <StatTrend trend="up">
            <ArrowUpRight size={16} />
            +2.3% from last month
          </StatTrend>
        </StatCard>

        <StatCard trend="up">
          <StatHeader>
            <StatLabel>Monthly Income</StatLabel>
            <StatIcon variant="profit">
              <TrendingUp size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>$5,240.00</StatValue>
          <StatTrend trend="up">
            <ArrowUpRight size={16} />
            +8.1% from last month
          </StatTrend>
        </StatCard>

        <StatCard trend="down">
          <StatHeader>
            <StatLabel>Monthly Expenses</StatLabel>
            <StatIcon variant="loss">
              <CreditCard size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>$3,127.45</StatValue>
          <StatTrend trend="down">
            <ArrowDownRight size={16} />
            -5.2% from last month
          </StatTrend>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatLabel>Savings Goal</StatLabel>
            <StatIcon variant="warning">
              <Target size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>68%</StatValue>
          <StatTrend trend="up">
            <ArrowUpRight size={16} />
            On track for 2024
          </StatTrend>
        </StatCard>
      </StatsGrid>

      {/* AI Assistant Chat */}
      <DashboardChatInterface />

      {/* Charts */}
      <ChartsGrid>
        <ChartCard>
          <ChartTitle>Spending Trends (Last 6 Months)</ChartTitle>
          <PlaceholderChart height="300px">
            <PlaceholderContent>
              <TrendingUp size={48} />
              <div>Interactive Line Chart</div>
              <small>Coming Soon</small>
            </PlaceholderContent>
          </PlaceholderChart>
        </ChartCard>

        <ChartCard>
          <ChartTitle>Category Breakdown</ChartTitle>
          <PlaceholderChart height="300px">
            <PlaceholderContent>
              <Target size={48} />
              <div>Pie Chart</div>
              <small>Coming Soon</small>
            </PlaceholderContent>
          </PlaceholderChart>
        </ChartCard>
      </ChartsGrid>

      {/* Recent Activity */}
      <ActivitySection>
        <ChartTitle>Recent Transactions</ChartTitle>
        <ActivityList>
          <ActivityItem>
            <ActivityInfo>
              <StatIcon variant="profit">
                <ArrowUpRight size={16} />
              </StatIcon>
              <ActivityDetails>
                <ActivityTitle>Salary Deposit</ActivityTitle>
                <ActivityMeta>Today • Direct Deposit</ActivityMeta>
              </ActivityDetails>
            </ActivityInfo>
            <ActivityAmount type="income">+$2,500.00</ActivityAmount>
          </ActivityItem>

          <ActivityItem>
            <ActivityInfo>
              <StatIcon variant="loss">
                <ArrowDownRight size={16} />
              </StatIcon>
              <ActivityDetails>
                <ActivityTitle>Grocery Shopping</ActivityTitle>
                <ActivityMeta>Yesterday • Whole Foods Market</ActivityMeta>
              </ActivityDetails>
            </ActivityInfo>
            <ActivityAmount type="expense">-$127.43</ActivityAmount>
          </ActivityItem>

          <ActivityItem>
            <ActivityInfo>
              <StatIcon variant="loss">
                <CreditCard size={16} />
              </StatIcon>
              <ActivityDetails>
                <ActivityTitle>Utility Bill</ActivityTitle>
                <ActivityMeta>3 days ago • Pacific Gas & Electric</ActivityMeta>
              </ActivityDetails>
            </ActivityInfo>
            <ActivityAmount type="expense">-$89.32</ActivityAmount>
          </ActivityItem>

          <ActivityItem>
            <ActivityInfo>
              <StatIcon variant="primary">
                <DollarSign size={16} />
              </StatIcon>
              <ActivityDetails>
                <ActivityTitle>Investment Return</ActivityTitle>
                <ActivityMeta>1 week ago • Portfolio Dividend</ActivityMeta>
              </ActivityDetails>
            </ActivityInfo>
            <ActivityAmount type="income">+$45.67</ActivityAmount>
          </ActivityItem>
        </ActivityList>
      </ActivitySection>
    </DashboardContainer>
  )
}

export default DashboardPage