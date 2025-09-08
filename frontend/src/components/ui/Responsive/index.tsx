import React, { useState, useEffect } from 'react'
import styled, { css } from 'styled-components'

// Breakpoint utilities
export const breakpoints = {
  xs: 475,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const

export type Breakpoint = keyof typeof breakpoints

// Hook for responsive behavior
export const useBreakpoint = (): Breakpoint => {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('xs')

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth
      
      if (width >= breakpoints['2xl']) {
        setBreakpoint('2xl')
      } else if (width >= breakpoints.xl) {
        setBreakpoint('xl')
      } else if (width >= breakpoints.lg) {
        setBreakpoint('lg')
      } else if (width >= breakpoints.md) {
        setBreakpoint('md')
      } else if (width >= breakpoints.sm) {
        setBreakpoint('sm')
      } else {
        setBreakpoint('xs')
      }
    }

    updateBreakpoint()
    window.addEventListener('resize', updateBreakpoint)
    
    return () => window.removeEventListener('resize', updateBreakpoint)
  }, [])

  return breakpoint
}

// Hook to check if screen size matches a breakpoint
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const media = window.matchMedia(query)
    if (media.matches !== matches) {
      setMatches(media.matches)
    }
    
    const listener = () => setMatches(media.matches)
    media.addEventListener('change', listener)
    
    return () => media.removeEventListener('change', listener)
  }, [matches, query])

  return matches
}

// Responsive container component
interface ResponsiveContainerProps {
  children: React.ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  padding?: boolean
  className?: string
  'data-testid'?: string
}

const Container = styled.div.withConfig({
  shouldForwardProp: (prop) => !['maxWidth', 'padding'].includes(prop as string),
})<Pick<ResponsiveContainerProps, 'maxWidth' | 'padding'>>`
  width: 100%;
  margin: 0 auto;
  
  ${({ maxWidth, theme }) => {
    switch (maxWidth) {
      case 'sm':
        return css`max-width: ${theme.breakpoints.sm};`
      case 'md':
        return css`max-width: ${theme.breakpoints.md};`
      case 'lg':
        return css`max-width: ${theme.breakpoints.lg};`
      case 'xl':
        return css`max-width: ${theme.breakpoints.xl};`
      case '2xl':
        return css`max-width: ${theme.breakpoints['2xl']};`
      case 'full':
        return css`max-width: none;`
      default:
        return css`max-width: ${theme.breakpoints.lg};`
    }
  }}
  
  ${({ padding, theme }) => padding && css`
    padding: 0 ${theme.spacing[4]};
    
    @media (min-width: ${theme.breakpoints.sm}) {
      padding: 0 ${theme.spacing[6]};
    }
    
    @media (min-width: ${theme.breakpoints.lg}) {
      padding: 0 ${theme.spacing[8]};
    }
  `}
`

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  maxWidth = 'lg',
  padding = true,
  className,
  'data-testid': testId
}) => (
  <Container maxWidth={maxWidth} padding={padding} className={className} data-testid={testId}>
    {children}
  </Container>
)

// Responsive grid system
interface GridProps {
  children: React.ReactNode
  cols?: {
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
    '2xl'?: number
  }
  gap?: number | string
  className?: string
  'data-testid'?: string
}

const GridContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => !['cols', 'gap'].includes(prop as string),
})<Pick<GridProps, 'cols' | 'gap'>>`
  display: grid;
  gap: ${({ gap, theme }) => 
    typeof gap === 'number' ? theme.spacing[gap as keyof typeof theme.spacing] : gap || theme.spacing[4]};
  
  /* Default to 1 column on mobile */
  grid-template-columns: 1fr;
  
  ${({ cols, theme }) => {
    if (!cols) return ''
    
    return Object.entries(cols)
      .map(([breakpoint, columns]) => {
        if (breakpoint === 'xs') {
          return css`
            grid-template-columns: repeat(${columns}, 1fr);
          `
        }
        
        return css`
          @media (min-width: ${theme.breakpoints[breakpoint as keyof typeof theme.breakpoints]}) {
            grid-template-columns: repeat(${columns}, 1fr);
          }
        `
      })
      .join('')
  }}
`

export const Grid: React.FC<GridProps> = ({
  children,
  cols = { xs: 1, sm: 2, lg: 3 },
  gap = 4,
  className,
  'data-testid': testId
}) => (
  <GridContainer cols={cols} gap={gap} className={className} data-testid={testId}>
    {children}
  </GridContainer>
)

// Show/Hide components based on breakpoints
interface ShowProps {
  children: React.ReactNode
  above?: Breakpoint
  below?: Breakpoint
  only?: Breakpoint
}

const BreakpointContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => !['above', 'below', 'only'].includes(prop as string),
})<Pick<ShowProps, 'above' | 'below' | 'only'>>`
  ${({ above, theme }) => above && css`
    display: none;
    
    @media (min-width: ${theme.breakpoints[above]}) {
      display: block;
    }
  `}
  
  ${({ below, theme }) => below && css`
    display: block;
    
    @media (min-width: ${theme.breakpoints[below]}) {
      display: none;
    }
  `}
  
  ${({ only, theme }) => only && css`
    display: none;
    
    @media (min-width: ${theme.breakpoints[only]}) {
      display: block;
    }
    
    @media (min-width: ${theme.breakpoints[
      only === 'xs' ? 'sm' :
      only === 'sm' ? 'md' :
      only === 'md' ? 'lg' :
      only === 'lg' ? 'xl' :
      '2xl'
    ]}) {
      display: none;
    }
  `}
`

export const Show: React.FC<ShowProps> = ({ children, ...props }) => (
  <BreakpointContainer {...props}>
    {children}
  </BreakpointContainer>
)

export const Hide: React.FC<ShowProps> = ({ children, above, below, only }) => {
  // Invert the logic for Hide component
  if (above) {
    return (
      <BreakpointContainer below={above}>
        {children}
      </BreakpointContainer>
    )
  }
  
  if (below) {
    return (
      <BreakpointContainer above={below}>
        {children}
      </BreakpointContainer>
    )
  }
  
  if (only) {
    // For "only", we show everywhere except that breakpoint
    return (
      <BreakpointContainer above={only}>
        <BreakpointContainer below={only}>
          {children}
        </BreakpointContainer>
      </BreakpointContainer>
    )
  }
  
  return <>{children}</>
}

// Responsive spacing utilities
interface SpacingProps {
  children: React.ReactNode
  p?: number | { xs?: number; sm?: number; md?: number; lg?: number }
  m?: number | { xs?: number; sm?: number; md?: number; lg?: number }
  className?: string
  'data-testid'?: string
}

const SpacingContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => !['p', 'm'].includes(prop as string),
})<Pick<SpacingProps, 'p' | 'm'>>`
  ${({ p, theme }) => {
    if (typeof p === 'number') {
      return css`padding: ${theme.spacing[p as keyof typeof theme.spacing]};`
    }
    
    if (p && typeof p === 'object') {
      return Object.entries(p)
        .map(([breakpoint, value]) => {
          if (breakpoint === 'xs') {
            return css`padding: ${theme.spacing[value as keyof typeof theme.spacing]};`
          }
          
          return css`
            @media (min-width: ${theme.breakpoints[breakpoint as keyof typeof theme.breakpoints]}) {
              padding: ${theme.spacing[value as keyof typeof theme.spacing]};
            }
          `
        })
        .join('')
    }
  }}
  
  ${({ m, theme }) => {
    if (typeof m === 'number') {
      return css`margin: ${theme.spacing[m as keyof typeof theme.spacing]};`
    }
    
    if (m && typeof m === 'object') {
      return Object.entries(m)
        .map(([breakpoint, value]) => {
          if (breakpoint === 'xs') {
            return css`margin: ${theme.spacing[value as keyof typeof theme.spacing]};`
          }
          
          return css`
            @media (min-width: ${theme.breakpoints[breakpoint as keyof typeof theme.breakpoints]}) {
              margin: ${theme.spacing[value as keyof typeof theme.spacing]};
            }
          `
        })
        .join('')
    }
  }}
`

export const Spacing: React.FC<SpacingProps> = ({
  children,
  p,
  m,
  className,
  'data-testid': testId
}) => (
  <SpacingContainer p={p} m={m} className={className} data-testid={testId}>
    {children}
  </SpacingContainer>
)

// Responsive aspect ratio component
interface AspectRatioProps {
  children: React.ReactNode
  ratio?: number // width / height (e.g., 16/9 = 1.777)
  className?: string
  'data-testid'?: string
}

const AspectRatioContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'ratio',
})<Pick<AspectRatioProps, 'ratio'>>`
  position: relative;
  width: 100%;
  padding-bottom: ${({ ratio }) => `${100 / (ratio || 1)}%`};
  overflow: hidden;
  
  > * {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`

export const AspectRatio: React.FC<AspectRatioProps> = ({
  children,
  ratio = 16/9,
  className,
  'data-testid': testId
}) => (
  <AspectRatioContainer ratio={ratio} className={className} data-testid={testId}>
    {children}
  </AspectRatioContainer>
)

// Responsive helper functions for styled-components
export const mediaQuery = {
  above: (breakpoint: Breakpoint) => `@media (min-width: ${breakpoints[breakpoint]}px)`,
  below: (breakpoint: Breakpoint) => `@media (max-width: ${breakpoints[breakpoint] - 1}px)`,
  between: (min: Breakpoint, max: Breakpoint) => 
    `@media (min-width: ${breakpoints[min]}px) and (max-width: ${breakpoints[max] - 1}px)`,
  only: (breakpoint: Breakpoint) => {
    const nextBreakpoint = 
      breakpoint === 'xs' ? 'sm' :
      breakpoint === 'sm' ? 'md' :
      breakpoint === 'md' ? 'lg' :
      breakpoint === 'lg' ? 'xl' :
      '2xl'
    
    return breakpoint === '2xl' 
      ? `@media (min-width: ${breakpoints[breakpoint]}px)`
      : `@media (min-width: ${breakpoints[breakpoint]}px) and (max-width: ${breakpoints[nextBreakpoint] - 1}px)`
  }
}