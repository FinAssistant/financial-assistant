import React from 'react'
import styled, { css } from 'styled-components'
import { AlertTriangle, CheckCircle, Info, X, XCircle } from 'lucide-react'

interface AlertProps {
  children: React.ReactNode
  variant?: 'info' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'base' | 'lg'
  dismissible?: boolean
  onDismiss?: () => void
  className?: string
  title?: string
  'data-testid'?: string
}

const AlertContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => !['variant', 'size', 'dismissible'].includes(prop as string),
})<Pick<AlertProps, 'variant' | 'size' | 'dismissible'>>`
  display: flex;
  gap: ${({ theme }) => theme.spacing[3]};
  border-radius: ${({ theme }) => theme.radii.md};
  border: 1px solid;
  position: relative;
  
  ${({ size, theme }) => {
    switch (size) {
      case 'sm':
        return css`
          padding: ${theme.spacing[3]} ${theme.spacing[4]};
        `
      case 'base':
        return css`
          padding: ${theme.spacing[4]} ${theme.spacing[5]};
        `
      case 'lg':
        return css`
          padding: ${theme.spacing[5]} ${theme.spacing[6]};
        `
      default:
        return css`
          padding: ${theme.spacing[4]} ${theme.spacing[5]};
        `
    }
  }}
  
  ${({ variant, theme }) => {
    switch (variant) {
      case 'info':
        return css`
          background: ${theme.colors.primary[50]};
          border-color: ${theme.colors.primary[200]};
          color: ${theme.colors.primary[800]};
        `
      case 'success':
        return css`
          background: ${theme.colors.success[50]};
          border-color: ${theme.colors.success[200]};
          color: ${theme.colors.success[800]};
        `
      case 'warning':
        return css`
          background: ${theme.colors.warning[50]};
          border-color: ${theme.colors.warning[200]};
          color: ${theme.colors.warning[800]};
        `
      case 'error':
        return css`
          background: ${theme.colors.error[50]};
          border-color: ${theme.colors.error[200]};
          color: ${theme.colors.error[800]};
        `
      default:
        return css`
          background: ${theme.colors.primary[50]};
          border-color: ${theme.colors.primary[200]};
          color: ${theme.colors.primary[800]};
        `
    }
  }}
  
  ${({ dismissible, theme }) => dismissible && css`
    padding-right: ${theme.spacing[12]};
  `}
`

const AlertIcon = styled.div`
  display: flex;
  align-items: flex-start;
  flex-shrink: 0;
  margin-top: 0.125rem;
`

const AlertContent = styled.div`
  flex: 1;
  min-width: 0;
`

const AlertTitle = styled.div`
  font-weight: ${({ theme }) => theme.fontWeights.semibold};
  margin-bottom: ${({ theme }) => theme.spacing[1]};
  font-size: ${({ theme }) => theme.fontSizes.sm};
`

const AlertMessage = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  line-height: ${({ theme }) => theme.lineHeights.relaxed};
`

const DismissButton = styled.button`
  position: absolute;
  top: ${({ theme }) => theme.spacing[2]};
  right: ${({ theme }) => theme.spacing[2]};
  background: none;
  border: none;
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing[1]};
  border-radius: ${({ theme }) => theme.radii.sm};
  color: inherit;
  opacity: 0.7;
  transition: ${({ theme }) => theme.transitions.fast};
  
  &:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.05);
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px currentColor;
  }
`

const getIcon = (variant: AlertProps['variant']) => {
  switch (variant) {
    case 'info':
      return <Info size={20} />
    case 'success':
      return <CheckCircle size={20} />
    case 'warning':
      return <AlertTriangle size={20} />
    case 'error':
      return <XCircle size={20} />
    default:
      return <Info size={20} />
  }
}

export const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'info',
  size = 'base',
  dismissible = false,
  onDismiss,
  className,
  title,
  'data-testid': testId
}) => {
  return (
    <AlertContainer
      variant={variant}
      size={size}
      dismissible={dismissible}
      className={className}
      data-testid={testId}
      role="alert"
    >
      <AlertIcon>
        {getIcon(variant)}
      </AlertIcon>
      
      <AlertContent>
        {title && <AlertTitle>{title}</AlertTitle>}
        <AlertMessage>{children}</AlertMessage>
      </AlertContent>
      
      {dismissible && onDismiss && (
        <DismissButton
          onClick={onDismiss}
          aria-label="Dismiss alert"
          type="button"
        >
          <X size={16} />
        </DismissButton>
      )}
    </AlertContainer>
  )
}

// Specialized Alert components
export const InfoAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert {...props} variant="info" />
)

export const SuccessAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert {...props} variant="success" />
)

export const WarningAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert {...props} variant="warning" />
)

export const ErrorAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert {...props} variant="error" />
)

export default Alert