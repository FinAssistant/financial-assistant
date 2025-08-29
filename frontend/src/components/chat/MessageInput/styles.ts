import styled, { css } from 'styled-components'
import Button from '../../ui/Button'

export const MessageInputContainer = styled.div`
  border-top: 1px solid ${({ theme }) => theme.colors.border.light};
  background: ${({ theme }) => theme.colors.background.primary};
  padding: ${({ theme }) => theme.spacing.md};
  
  @media (max-width: ${({ theme }) => theme.breakpoints.md}) {
    padding: ${({ theme }) => theme.spacing.sm};
  }
`

export const InputWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.sm};
  background: ${({ theme }) => theme.colors.background.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: ${({ theme }) => theme.spacing.sm};
  
  &:focus-within {
    border-color: ${({ theme }) => theme.colors.primary.main};
    box-shadow: 0 0 0 2px ${({ theme }) => theme.colors.primary.main}20;
  }
`

export const TextArea = styled.textarea`
  border: none;
  outline: none;
  background: transparent;
  resize: none;
  font-family: ${({ theme }) => theme.fonts.primary};
  font-size: ${({ theme }) => theme.fontSizes.base};
  color: ${({ theme }) => theme.colors.text.primary};
  line-height: 1.5;
  min-height: 20px;
  max-height: 120px;
  overflow-y: auto;
  
  &::placeholder {
    color: ${({ theme }) => theme.colors.text.muted};
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    
    &::placeholder {
      color: ${({ theme }) => theme.colors.text.muted};
    }
  }
  
  /* Custom scrollbar for textarea */
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.colors.border.light};
    border-radius: ${({ theme }) => theme.radii.sm};
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: ${({ theme }) => theme.colors.border.medium};
  }
`

export const InputActions = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}) {
    flex-wrap: wrap;
    gap: ${({ theme }) => theme.spacing.xs};
  }
`

export const CharacterCount = styled.span.withConfig({
  shouldForwardProp: (prop) => prop !== 'isOverLimit',
})<{ isOverLimit: boolean }>`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-family: ${({ theme }) => theme.fonts.mono};
  color: ${({ theme, isOverLimit }) => 
    isOverLimit ? theme.colors.error.main : theme.colors.text.muted};
  
  ${({ isOverLimit }) => isOverLimit && css`
    font-weight: ${({ theme }) => theme.fontWeights.medium};
  `}
`

export const SendButton = styled(Button)`
  min-width: 60px;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}) {
    min-width: 50px;
    font-size: ${({ theme }) => theme.fontSizes.sm};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`