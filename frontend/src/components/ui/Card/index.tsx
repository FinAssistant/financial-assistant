import React from 'react'
import styled, { css } from 'styled-components'

interface CardProps {
  children: React.ReactNode
  variant?: 'default' | 'outlined' | 'elevated'
  size?: 'sm' | 'base' | 'lg'
  hover?: boolean
  className?: string
  onClick?: () => void
  'data-testid'?: string
}

const StyledCard = styled.div.withConfig({
  shouldForwardProp: (prop) => !['variant', 'size', 'hover'].includes(prop as string),
})<CardProps & { 'data-testid'?: string }>`
  background: ${({ theme }) => theme.colors.background.card};
  border-radius: ${({ theme }) => theme.radii.card};
  transition: ${({ theme }) => theme.transitions.normal};
  
  ${({ size, theme }) => {
    switch (size) {
      case 'sm':
        return css`
          padding: ${theme.components.card.padding.sm};
        `
      case 'base':
        return css`
          padding: ${theme.components.card.padding.base};
        `
      case 'lg':
        return css`
          padding: ${theme.components.card.padding.lg};
        `
      default:
        return css`
          padding: ${theme.components.card.padding.base};
        `
    }
  }}
  
  ${({ variant, theme }) => {
    switch (variant) {
      case 'outlined':
        return css`
          border: 1px solid ${theme.colors.border.light};
          box-shadow: none;
        `
      case 'elevated':
        return css`
          border: 1px solid ${theme.colors.border.light};
          box-shadow: ${theme.shadows.card};
        `
      default:
        return css`
          border: 1px solid ${theme.colors.border.light};
          box-shadow: ${theme.shadows.card};
        `
    }
  }}
  
  ${({ hover, theme }) => hover && css`
    cursor: pointer;
    
    &:hover {
      box-shadow: ${theme.shadows.cardHover};
      transform: translateY(-1px);
    }
  `}
  
  ${({ onClick }) => onClick && css`
    cursor: pointer;
  `}
`

const CardHeader = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing[4]};
  
  &:last-child {
    margin-bottom: 0;
  }
`

const CardBody = styled.div`
  flex: 1;
`

const CardFooter = styled.div`
  margin-top: ${({ theme }) => theme.spacing[4]};
  
  &:first-child {
    margin-top: 0;
  }
`

export const Card: React.FC<CardProps> & {
  Header: typeof CardHeader
  Body: typeof CardBody
  Footer: typeof CardFooter
} = ({
  children,
  variant = 'default',
  size = 'base',
  hover = false,
  className,
  onClick,
  'data-testid': testId
}) => {
  return (
    <StyledCard
      variant={variant}
      size={size}
      hover={hover}
      className={className}
      onClick={onClick}
      data-testid={testId}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </StyledCard>
  )
}

Card.Header = CardHeader
Card.Body = CardBody
Card.Footer = CardFooter

export default Card