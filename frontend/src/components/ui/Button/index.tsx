import React from 'react'
import styled, { css } from 'styled-components'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'base' | 'lg'
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
  className?: string
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
}

const StyledButton = styled.button.withConfig({
  shouldForwardProp: (prop) => !['variant', 'size', 'fullWidth', 'loading', 'icon'].includes(prop as string),
})<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${({ theme, icon }) => icon ? theme.spacing[2] : '0'};
  font-family: ${({ theme }) => theme.fonts.primary};
  font-weight: ${({ theme }) => theme.fontWeights.medium};
  border: none;
  border-radius: ${({ theme }) => theme.radii.button};
  cursor: pointer;
  transition: ${({ theme }) => theme.transitions.normal};
  text-decoration: none;
  white-space: nowrap;
  user-select: none;
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px ${({ theme }) => theme.colors.border.focus}40;
  }
  
  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  ${({ size, theme }) => {
    switch (size) {
      case 'sm':
        return css`
          height: ${theme.components.button.height.sm};
          padding: ${theme.components.button.padding.sm};
          font-size: ${theme.fontSizes.sm};
        `
      case 'base':
        return css`
          height: ${theme.components.button.height.base};
          padding: ${theme.components.button.padding.base};
          font-size: ${theme.fontSizes.base};
        `
      case 'lg':
        return css`
          height: ${theme.components.button.height.lg};
          padding: ${theme.components.button.padding.lg};
          font-size: ${theme.fontSizes.lg};
        `
      default:
        return css`
          height: ${theme.components.button.height.base};
          padding: ${theme.components.button.padding.base};
          font-size: ${theme.fontSizes.base};
        `
    }
  }}
  
  ${({ variant, theme }) => {
    switch (variant) {
      case 'primary':
        return css`
          background: ${theme.colors.primary.main};
          color: ${theme.colors.text.inverse};
          
          &:hover:not(:disabled) {
            background: ${theme.colors.primary.dark};
          }
          
          &:active:not(:disabled) {
            background: ${theme.colors.primary[800]};
          }
        `
      case 'secondary':
        return css`
          background: ${theme.colors.secondary.main};
          color: ${theme.colors.text.inverse};
          
          &:hover:not(:disabled) {
            background: ${theme.colors.secondary.dark};
          }
          
          &:active:not(:disabled) {
            background: ${theme.colors.secondary[800]};
          }
        `
      case 'outline':
        return css`
          background: transparent;
          color: ${theme.colors.primary.main};
          border: 1px solid ${theme.colors.primary.main};
          
          &:hover:not(:disabled) {
            background: ${theme.colors.primary[50]};
          }
          
          &:active:not(:disabled) {
            background: ${theme.colors.primary[100]};
          }
        `
      case 'ghost':
        return css`
          background: transparent;
          color: ${theme.colors.text.primary};
          
          &:hover:not(:disabled) {
            background: ${theme.colors.secondary[100]};
          }
          
          &:active:not(:disabled) {
            background: ${theme.colors.secondary[200]};
          }
        `
      case 'danger':
        return css`
          background: ${theme.colors.error.main};
          color: ${theme.colors.text.inverse};
          
          &:hover:not(:disabled) {
            background: ${theme.colors.error.dark};
          }
          
          &:active:not(:disabled) {
            background: ${theme.colors.error[800]};
          }
        `
      default:
        return css`
          background: ${theme.colors.primary.main};
          color: ${theme.colors.text.inverse};
          
          &:hover:not(:disabled) {
            background: ${theme.colors.primary.dark};
          }
        `
    }
  }}
  
  ${({ fullWidth }) => fullWidth && css`
    width: 100%;
  `}
  
  ${({ loading }) => loading && css`
    pointer-events: none;
  `}
`

const LoadingSpinner = styled.div`
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'base',
  disabled = false,
  loading = false,
  fullWidth = false,
  className,
  onClick,
  type = 'button',
  icon,
  iconPosition = 'left'
}) => {
  const handleClick = () => {
    if (!disabled && !loading && onClick) {
      onClick()
    }
  }

  return (
    <StyledButton
      variant={variant}
      size={size}
      disabled={disabled || loading}
      fullWidth={fullWidth}
      className={className}
      onClick={handleClick}
      type={type}
      icon={icon}
    >
      {loading && <LoadingSpinner />}
      {!loading && icon && iconPosition === 'left' && icon}
      {!loading && children}
      {!loading && icon && iconPosition === 'right' && icon}
    </StyledButton>
  )
}

export default Button