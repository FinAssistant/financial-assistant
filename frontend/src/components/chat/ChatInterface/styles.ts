import styled from 'styled-components'
import { ThreadPrimitive } from '@assistant-ui/react'

export const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 500px;
  max-height: 500px;
  background: ${({ theme }) => theme.colors.background.card};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.card};
  box-shadow: ${({ theme }) => theme.shadows.card};
  overflow: hidden;

  @media (min-width: ${({ theme }) => theme.breakpoints.md}) {
    height: 600px;
    max-height: 600px;
  }
`

export const ChatHeader = styled.div`
  padding: ${({ theme }) => theme.spacing[4]};
  background: ${({ theme }) => theme.colors.background.secondary};
  border-bottom: 1px solid ${({ theme }) => theme.colors.border.light};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing[2]};
`

export const ChatTitle = styled.h3`
  margin: 0;
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: ${({ theme }) => theme.fontWeights.semibold};
  color: ${({ theme }) => theme.colors.text.primary};
  font-family: ${({ theme }) => theme.fonts.heading};
`

// Styled wrapper for Assistant UI Thread component
export const StyledThread = styled(ThreadPrimitive.Root)`
  flex: 1;
  display: flex;
  flex-direction: column;
  
  /* Apply theme styling to Assistant UI components using data attributes */
  [data-message-role="user"] {
    [data-message-content] {
      background: ${({ theme }) => theme.colors.primary.main};
      color: ${({ theme }) => theme.colors.text.inverse};
      border-radius: ${({ theme }) => `${theme.radii.xl} ${theme.radii.xl} ${theme.radii.base} ${theme.radii.xl}`};
      padding: ${({ theme }) => theme.spacing[3]} ${({ theme }) => theme.spacing[4]};
      margin-left: auto;
      max-width: 85%;
      box-shadow: ${({ theme }) => theme.shadows.sm};
    }
  }

  [data-message-role="assistant"] {
    [data-message-content] {
      background: ${({ theme }) => theme.colors.background.secondary};
      color: ${({ theme }) => theme.colors.text.primary};
      border-radius: ${({ theme }) => `${theme.radii.xl} ${theme.radii.xl} ${theme.radii.xl} ${theme.radii.base}`};
      padding: ${({ theme }) => theme.spacing[3]} ${({ theme }) => theme.spacing[4]};
      margin-right: auto;
      max-width: 85%;
      box-shadow: ${({ theme }) => theme.shadows.sm};
    }
  }

  [data-composer-input] {
    padding: ${({ theme }) => theme.spacing[2]} ${({ theme }) => theme.spacing[3]};
    border: 1px solid ${({ theme }) => theme.colors.border.light};
    border-radius: ${({ theme }) => theme.radii.input};
    font-family: ${({ theme }) => theme.fonts.primary};
    font-size: ${({ theme }) => theme.fontSizes.base};
    
    &:focus {
      border-color: ${({ theme }) => theme.colors.border.focus};
      box-shadow: 0 0 0 2px ${({ theme }) => theme.colors.primary[100]};
    }
  }

  [data-composer-send] {
    background: ${({ theme }) => theme.colors.primary.main};
    color: ${({ theme }) => theme.colors.text.inverse};
    border-radius: ${({ theme }) => theme.radii.base};
    
    &:hover {
      background: ${({ theme }) => theme.colors.primary.dark};
    }
  }
`