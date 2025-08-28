import styled, { css, keyframes } from 'styled-components'

export const MessageListContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: ${({ theme }) => theme.spacing.md};
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.sm};
  
  /* Custom scrollbar */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: ${({ theme }) => theme.colors.background.secondary};
    border-radius: ${({ theme }) => theme.radii.sm};
  }
  
  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.colors.border.light};
    border-radius: ${({ theme }) => theme.radii.sm};
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: ${({ theme }) => theme.colors.border.medium};
  }
`

export const MessageContainer = styled.div<{ $isUser: boolean }>`
  display: flex;
  justify-content: ${({ $isUser }) => $isUser ? 'flex-end' : 'flex-start'};
  margin-bottom: ${({ theme }) => theme.spacing.xs};
`

export const MessageBubble = styled.div`
  max-width: 70%;
  min-width: 100px;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    max-width: 85%;
  }
  
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}) {
    max-width: 90%;
  }
`

const messageBase = css`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  border-radius: ${({ theme }) => theme.radii.lg};
  font-family: ${({ theme }) => theme.fonts.primary};
  font-size: ${({ theme }) => theme.fontSizes.base};
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
`

export const UserMessage = styled.div`
  ${messageBase}
  background: ${({ theme }) => theme.colors.primary.main};
  color: ${({ theme }) => theme.colors.text.inverse};
  border-bottom-right-radius: ${({ theme }) => theme.radii.sm};
`

export const AssistantMessage = styled.div`
  ${messageBase}
  background: ${({ theme }) => theme.colors.background.secondary};
  color: ${({ theme }) => theme.colors.text.primary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-bottom-left-radius: ${({ theme }) => theme.radii.sm};
`

export const MessageMeta = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: ${({ theme }) => theme.spacing.xs};
  padding: 0 ${({ theme }) => theme.spacing.xs};
`

export const MessageTime = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.text.muted};
  font-family: ${({ theme }) => theme.fonts.mono};
`

export const AgentLabel = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.primary.main};
  font-weight: ${({ theme }) => theme.fontWeights.medium};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`

const bounce = keyframes`
  0%, 60%, 100% {
    animation-timing-function: cubic-bezier(0.215, 0.61, 0.355, 1);
    transform: translate3d(0, 0, 0);
  }
  20%, 40% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -6px, 0);
  }
`

export const StreamingIndicator = styled.div`
  display: flex;
  gap: 4px;
  padding: ${({ theme }) => theme.spacing.xs};
  
  span {
    width: 6px;
    height: 6px;
    background: ${({ theme }) => theme.colors.primary.main};
    border-radius: 50%;
    animation: ${bounce} 1.4s ease-in-out infinite both;
    
    &:nth-child(1) {
      animation-delay: -0.32s;
    }
    
    &:nth-child(2) {
      animation-delay: -0.16s;
    }
    
    &:nth-child(3) {
      animation-delay: 0s;
    }
  }
`