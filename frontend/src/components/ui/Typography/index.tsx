import React from 'react'
import styled, { css } from 'styled-components'

// Typography component interfaces
interface TypographyProps {
  children: React.ReactNode
  color?: 'primary' | 'secondary' | 'tertiary' | 'muted' | 'inverse'
  align?: 'left' | 'center' | 'right' | 'justify'
  className?: string
}

interface HeadingProps extends TypographyProps {
  level?: 1 | 2 | 3 | 4 | 5 | 6
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold'
}

interface TextProps extends TypographyProps {
  size?: 'xs' | 'sm' | 'base' | 'lg' | 'xl'
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold'
  variant?: 'body' | 'caption' | 'overline'
}

// Base typography styles
const getColorStyles = (color?: TypographyProps['color']) => css`
  color: ${({ theme }) => {
    switch (color) {
      case 'primary':
        return theme.colors.text.primary
      case 'secondary':
        return theme.colors.text.secondary
      case 'tertiary':
        return theme.colors.text.tertiary
      case 'muted':
        return theme.colors.text.muted
      case 'inverse':
        return theme.colors.text.inverse
      default:
        return theme.colors.text.primary
    }
  }};
`

const getAlignStyles = (align?: TypographyProps['align']) => css`
  text-align: ${align || 'left'};
`

// Styled components
const StyledHeading = styled.h1.withConfig({
  shouldForwardProp: (prop) => !['level', 'weight', 'color', 'align'].includes(prop as string),
})<HeadingProps>`
  font-family: ${({ theme }) => theme.fonts.heading};
  font-weight: ${({ theme, weight }) => theme.fontWeights[weight || 'semibold']};
  line-height: ${({ theme }) => theme.lineHeights.tight};
  margin: 0;
  
  ${({ level, theme }) => {
    switch (level) {
      case 1:
        return css`
          font-size: ${theme.fontSizes['4xl']};
          letter-spacing: ${theme.letterSpacing.tight};
          @media (max-width: ${theme.breakpoints.md}) {
            font-size: ${theme.fontSizes['3xl']};
          }
        `
      case 2:
        return css`
          font-size: ${theme.fontSizes['3xl']};
          letter-spacing: ${theme.letterSpacing.tight};
          @media (max-width: ${theme.breakpoints.md}) {
            font-size: ${theme.fontSizes['2xl']};
          }
        `
      case 3:
        return css`
          font-size: ${theme.fontSizes['2xl']};
          @media (max-width: ${theme.breakpoints.md}) {
            font-size: ${theme.fontSizes.xl};
          }
        `
      case 4:
        return css`
          font-size: ${theme.fontSizes.xl};
          @media (max-width: ${theme.breakpoints.md}) {
            font-size: ${theme.fontSizes.lg};
          }
        `
      case 5:
        return css`
          font-size: ${theme.fontSizes.lg};
        `
      case 6:
        return css`
          font-size: ${theme.fontSizes.base};
          font-weight: ${theme.fontWeights.bold};
        `
      default:
        return css`
          font-size: ${theme.fontSizes['2xl']};
        `
    }
  }}
  
  ${({ color }) => getColorStyles(color)}
  ${({ align }) => getAlignStyles(align)}
`

const StyledText = styled.p.withConfig({
  shouldForwardProp: (prop) => !['size', 'weight', 'variant', 'color', 'align'].includes(prop as string),
})<TextProps>`
  font-family: ${({ theme }) => theme.fonts.primary};
  font-weight: ${({ theme, weight }) => theme.fontWeights[weight || 'normal']};
  line-height: ${({ theme }) => theme.lineHeights.normal};
  margin: 0;
  
  ${({ size, theme }) => {
    switch (size) {
      case 'xs':
        return css`
          font-size: ${theme.fontSizes.xs};
        `
      case 'sm':
        return css`
          font-size: ${theme.fontSizes.sm};
        `
      case 'base':
        return css`
          font-size: ${theme.fontSizes.base};
        `
      case 'lg':
        return css`
          font-size: ${theme.fontSizes.lg};
        `
      case 'xl':
        return css`
          font-size: ${theme.fontSizes.xl};
        `
      default:
        return css`
          font-size: ${theme.fontSizes.base};
        `
    }
  }}
  
  ${({ variant, theme }) => {
    switch (variant) {
      case 'caption':
        return css`
          font-size: ${theme.fontSizes.sm};
          color: ${theme.colors.text.secondary};
          line-height: ${theme.lineHeights.snug};
        `
      case 'overline':
        return css`
          font-size: ${theme.fontSizes.xs};
          font-weight: ${theme.fontWeights.medium};
          text-transform: uppercase;
          letter-spacing: ${theme.letterSpacing.wider};
          color: ${theme.colors.text.secondary};
        `
      default:
        return ''
    }
  }}
  
  ${({ color }) => getColorStyles(color)}
  ${({ align }) => getAlignStyles(align)}
`

// Component implementations
export const Heading: React.FC<HeadingProps> = ({ 
  children, 
  level = 2, 
  weight = 'semibold',
  color = 'primary',
  align = 'left',
  className 
}) => {
  return (
    <StyledHeading 
      as={`h${level}` as keyof JSX.IntrinsicElements}
      level={level}
      weight={weight}
      color={color}
      align={align}
      className={className}
    >
      {children}
    </StyledHeading>
  )
}

export const Text: React.FC<TextProps> = ({
  children,
  size = 'base',
  weight = 'normal',
  variant = 'body',
  color = 'primary',
  align = 'left',
  className
}) => {
  return (
    <StyledText
      size={size}
      weight={weight}
      variant={variant}
      color={color}
      align={align}
      className={className}
    >
      {children}
    </StyledText>
  )
}

// Specialized typography components
export const Caption: React.FC<Omit<TextProps, 'variant'>> = (props) => (
  <Text {...props} variant="caption" />
)

export const Overline: React.FC<Omit<TextProps, 'variant'>> = (props) => (
  <Text {...props} variant="overline" />
)

// Financial-specific typography components
const StyledCurrency = styled.span.withConfig({
  shouldForwardProp: (prop) => !['value', 'size', 'showSign'].includes(prop as string),
})<{ 
  value: number
  size?: 'sm' | 'base' | 'lg' | 'xl'
  showSign?: boolean
}>`
  font-family: ${({ theme }) => theme.fonts.mono};
  font-weight: ${({ theme }) => theme.fontWeights.medium};
  
  ${({ size, theme }) => {
    switch (size) {
      case 'sm':
        return css`font-size: ${theme.fontSizes.sm};`
      case 'base':
        return css`font-size: ${theme.fontSizes.base};`
      case 'lg':
        return css`font-size: ${theme.fontSizes.lg};`
      case 'xl':
        return css`font-size: ${theme.fontSizes.xl};`
      default:
        return css`font-size: ${theme.fontSizes.base};`
    }
  }}
  
  color: ${({ theme, value }) => 
    value > 0 
      ? theme.colors.profit.main 
      : value < 0 
      ? theme.colors.loss.main 
      : theme.colors.text.primary
  };
`

interface CurrencyProps {
  value: number
  currency?: string
  size?: 'sm' | 'base' | 'lg' | 'xl'
  showSign?: boolean
  className?: string
}

export const Currency: React.FC<CurrencyProps> = ({
  value,
  currency = 'USD',
  size = 'base',
  showSign = false,
  className
}) => {
  const formatCurrency = (amount: number) => {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
    
    const formatted = formatter.format(Math.abs(amount))
    const sign = showSign && amount > 0 ? '+' : amount < 0 ? '-' : ''
    
    return `${sign}${formatted}`
  }

  return (
    <StyledCurrency
      value={value}
      size={size}
      showSign={showSign}
      className={className}
    >
      {formatCurrency(value)}
    </StyledCurrency>
  )
}

const StyledPercentage = styled.span.withConfig({
  shouldForwardProp: (prop) => !['value', 'size'].includes(prop as string),
})<{ 
  value: number
  size?: 'sm' | 'base' | 'lg'
}>`
  font-family: ${({ theme }) => theme.fonts.mono};
  font-weight: ${({ theme }) => theme.fontWeights.medium};
  
  ${({ size, theme }) => {
    switch (size) {
      case 'sm':
        return css`font-size: ${theme.fontSizes.sm};`
      case 'base':
        return css`font-size: ${theme.fontSizes.base};`
      case 'lg':
        return css`font-size: ${theme.fontSizes.lg};`
      default:
        return css`font-size: ${theme.fontSizes.base};`
    }
  }}
  
  color: ${({ theme, value }) => 
    value > 0 
      ? theme.colors.profit.main 
      : value < 0 
      ? theme.colors.loss.main 
      : theme.colors.text.primary
  };
`

interface PercentageProps {
  value: number
  size?: 'sm' | 'base' | 'lg'
  decimals?: number
  showSign?: boolean
  className?: string
}

export const Percentage: React.FC<PercentageProps> = ({
  value,
  size = 'base',
  decimals = 2,
  showSign = true,
  className
}) => {
  const formatPercentage = (val: number) => {
    const sign = showSign && val > 0 ? '+' : ''
    return `${sign}${val.toFixed(decimals)}%`
  }

  return (
    <StyledPercentage
      value={value}
      size={size}
      className={className}
    >
      {formatPercentage(value)}
    </StyledPercentage>
  )
}