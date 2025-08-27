import React from 'react'
import styled, { keyframes, css } from 'styled-components'

// Loading animations
const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
`

const bounce = keyframes`
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-10px); }
`

const wave = keyframes`
  0%, 40%, 100% { transform: scaleY(0.4); }
  20% { transform: scaleY(1); }
`

// Spinner Component
interface SpinnerProps {
  size?: 'sm' | 'base' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'white'
  className?: string
  'data-testid'?: string
}

const StyledSpinner = styled.div.withConfig({
  shouldForwardProp: (prop) => !['size', 'color'].includes(prop as string),
})<SpinnerProps>`
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
  
  ${({ size }) => {
    switch (size) {
      case 'sm':
        return css`
          width: 1rem;
          height: 1rem;
          border-width: 2px;
        `
      case 'base':
        return css`
          width: 1.5rem;
          height: 1.5rem;
          border-width: 2px;
        `
      case 'lg':
        return css`
          width: 2rem;
          height: 2rem;
          border-width: 3px;
        `
      case 'xl':
        return css`
          width: 3rem;
          height: 3rem;
          border-width: 4px;
        `
      default:
        return css`
          width: 1.5rem;
          height: 1.5rem;
          border-width: 2px;
        `
    }
  }}
  
  ${({ color, theme }) => {
    switch (color) {
      case 'primary':
        return css`
          border-top: 2px solid ${theme.colors.primary.main};
          border-right: 2px solid ${theme.colors.primary.main};
        `
      case 'secondary':
        return css`
          border-top: 2px solid ${theme.colors.secondary.main};
          border-right: 2px solid ${theme.colors.secondary.main};
        `
      case 'white':
        return css`
          border-top: 2px solid ${theme.colors.text.inverse};
          border-right: 2px solid ${theme.colors.text.inverse};
        `
      default:
        return css`
          border-top: 2px solid ${theme.colors.primary.main};
          border-right: 2px solid ${theme.colors.primary.main};
        `
    }
  }}
`

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'base',
  color = 'primary',
  className,
  'data-testid': testId
}) => (
  <StyledSpinner 
    size={size} 
    color={color} 
    className={className} 
    data-testid={testId}
    role="status" 
    aria-label="Loading" 
  />
)

// Dots Loading Component
interface DotsProps {
  size?: 'sm' | 'base' | 'lg'
  color?: 'primary' | 'secondary'
  className?: string
  'data-testid'?: string
}

const DotsContainer = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
`

const Dot = styled.div.withConfig({
  shouldForwardProp: (prop) => !['size', 'color', 'delay'].includes(prop as string),
})<DotsProps & { delay: number }>`
  border-radius: 50%;
  animation: ${bounce} 1.4s ease-in-out infinite both;
  animation-delay: ${({ delay }) => delay}s;
  
  ${({ size }) => {
    switch (size) {
      case 'sm':
        return css`
          width: 0.5rem;
          height: 0.5rem;
        `
      case 'base':
        return css`
          width: 0.75rem;
          height: 0.75rem;
        `
      case 'lg':
        return css`
          width: 1rem;
          height: 1rem;
        `
      default:
        return css`
          width: 0.75rem;
          height: 0.75rem;
        `
    }
  }}
  
  ${({ color, theme }) => {
    switch (color) {
      case 'primary':
        return css`background: ${theme.colors.primary.main};`
      case 'secondary':
        return css`background: ${theme.colors.secondary.main};`
      default:
        return css`background: ${theme.colors.primary.main};`
    }
  }}
`

export const LoadingDots: React.FC<DotsProps> = ({
  size = 'base',
  color = 'primary',
  className,
  'data-testid': testId
}) => (
  <DotsContainer className={className} data-testid={testId} role="status" aria-label="Loading">
    <Dot size={size} color={color} delay={0} />
    <Dot size={size} color={color} delay={0.1} />
    <Dot size={size} color={color} delay={0.2} />
  </DotsContainer>
)

// Wave Loading Component
const WaveContainer = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
`

const Wave = styled.div.withConfig({
  shouldForwardProp: (prop) => !['size', 'color', 'delay'].includes(prop as string),
})<DotsProps & { delay: number }>`
  border-radius: 2px;
  animation: ${wave} 1.2s ease-in-out infinite;
  animation-delay: ${({ delay }) => delay}s;
  
  ${({ size }) => {
    switch (size) {
      case 'sm':
        return css`
          width: 0.125rem;
          height: 1rem;
        `
      case 'base':
        return css`
          width: 0.25rem;
          height: 1.5rem;
        `
      case 'lg':
        return css`
          width: 0.375rem;
          height: 2rem;
        `
      default:
        return css`
          width: 0.25rem;
          height: 1.5rem;
        `
    }
  }}
  
  ${({ color, theme }) => {
    switch (color) {
      case 'primary':
        return css`background: ${theme.colors.primary.main};`
      case 'secondary':
        return css`background: ${theme.colors.secondary.main};`
      default:
        return css`background: ${theme.colors.primary.main};`
    }
  }}
`

export const LoadingWave: React.FC<DotsProps> = ({
  size = 'base',
  color = 'primary',
  className,
  'data-testid': testId
}) => (
  <WaveContainer className={className} data-testid={testId} role="status" aria-label="Loading">
    <Wave size={size} color={color} delay={0} />
    <Wave size={size} color={color} delay={0.1} />
    <Wave size={size} color={color} delay={0.2} />
    <Wave size={size} color={color} delay={0.3} />
    <Wave size={size} color={color} delay={0.4} />
  </WaveContainer>
)

// Skeleton Loading Component
interface SkeletonProps {
  width?: string
  height?: string
  variant?: 'text' | 'circular' | 'rectangular'
  className?: string
  'data-testid'?: string
}

const skeletonPulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
`

const StyledSkeleton = styled.div.withConfig({
  shouldForwardProp: (prop) => !['width', 'height', 'variant'].includes(prop as string),
})<SkeletonProps>`
  background: ${({ theme }) => theme.colors.secondary[200]};
  animation: ${skeletonPulse} 2s ease-in-out infinite;
  
  ${({ variant }) => {
    switch (variant) {
      case 'text':
        return css`
          height: 1rem;
          border-radius: 4px;
        `
      case 'circular':
        return css`
          border-radius: 50%;
        `
      case 'rectangular':
        return css`
          border-radius: 4px;
        `
      default:
        return css`
          border-radius: 4px;
        `
    }
  }}
  
  width: ${({ width }) => width || '100%'};
  height: ${({ height, variant }) => {
    if (height) return height
    return variant === 'text' ? '1rem' : '3rem'
  }};
`

export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  variant = 'rectangular',
  className,
  'data-testid': testId
}) => (
  <StyledSkeleton
    width={width}
    height={height}
    variant={variant}
    className={className}
    data-testid={testId}
    role="status"
    aria-label="Loading content"
  />
)

// Full Page Loading Component
interface PageLoadingProps {
  message?: string
  size?: 'base' | 'lg' | 'xl'
}

const PageLoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: ${({ theme }) => theme.spacing[4]};
`

const LoadingMessage = styled.div`
  color: ${({ theme }) => theme.colors.text.secondary};
  font-size: ${({ theme }) => theme.fontSizes.base};
  text-align: center;
`

export const PageLoading: React.FC<PageLoadingProps> = ({
  message = 'Loading...',
  size = 'lg'
}) => (
  <PageLoadingContainer>
    <Spinner size={size} />
    {message && <LoadingMessage>{message}</LoadingMessage>}
  </PageLoadingContainer>
)

// Overlay Loading Component
interface OverlayLoadingProps {
  message?: string
  isVisible: boolean
}

const OverlayContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'isVisible',
})<{ isVisible: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: ${({ theme }) => theme.colors.background.overlay};
  display: ${({ isVisible }) => isVisible ? 'flex' : 'none'};
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: ${({ theme }) => theme.spacing[4]};
  z-index: ${({ theme }) => theme.zIndex.overlay};
`

const OverlayContent = styled.div`
  background: ${({ theme }) => theme.colors.background.card};
  padding: ${({ theme }) => theme.spacing[8]};
  border-radius: ${({ theme }) => theme.radii.lg};
  box-shadow: ${({ theme }) => theme.shadows.modal};
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: ${({ theme }) => theme.spacing[4]};
  max-width: 20rem;
  text-align: center;
`

export const OverlayLoading: React.FC<OverlayLoadingProps> = ({
  message = 'Loading...',
  isVisible
}) => {
  if (!isVisible) return null
  
  return (
    <OverlayContainer isVisible={isVisible}>
      <OverlayContent>
        <Spinner size="xl" />
        <LoadingMessage>{message}</LoadingMessage>
      </OverlayContent>
    </OverlayContainer>
  )
}