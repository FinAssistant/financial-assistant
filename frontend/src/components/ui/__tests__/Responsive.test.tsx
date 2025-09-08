import { screen } from '@testing-library/react'
import { renderWithProviders } from '../../../tests/setupTests'
import { 
  ResponsiveContainer, 
  Grid, 
  Show, 
  Hide, 
  Spacing, 
  AspectRatio 
} from '../Responsive'

// Mock window.matchMedia for tests
const mockMatchMedia = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  addListener: jest.fn(),
  removeListener: jest.fn(),
  dispatchEvent: jest.fn(),
})

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(mockMatchMedia),
})

describe('Responsive Components', () => {
  describe('ResponsiveContainer', () => {
    it('renders container with children', () => {
      renderWithProviders(
        <ResponsiveContainer>
          <div>Container content</div>
        </ResponsiveContainer>
      )
      
      expect(screen.getByText('Container content')).toBeInTheDocument()
    })

    it('renders with different max widths', () => {
      renderWithProviders(
        <>
          <ResponsiveContainer maxWidth="sm" data-testid="sm-container">
            Small container
          </ResponsiveContainer>
          <ResponsiveContainer maxWidth="lg" data-testid="lg-container">
            Large container
          </ResponsiveContainer>
          <ResponsiveContainer maxWidth="full" data-testid="full-container">
            Full container
          </ResponsiveContainer>
        </>
      )
      
      expect(screen.getByTestId('sm-container')).toBeInTheDocument()
      expect(screen.getByTestId('lg-container')).toBeInTheDocument()
      expect(screen.getByTestId('full-container')).toBeInTheDocument()
    })

    it('renders with and without padding', () => {
      renderWithProviders(
        <>
          <ResponsiveContainer padding={true} data-testid="with-padding">
            With padding
          </ResponsiveContainer>
          <ResponsiveContainer padding={false} data-testid="without-padding">
            Without padding
          </ResponsiveContainer>
        </>
      )
      
      expect(screen.getByTestId('with-padding')).toBeInTheDocument()
      expect(screen.getByTestId('without-padding')).toBeInTheDocument()
    })
  })

  describe('Grid', () => {
    it('renders grid with children', () => {
      renderWithProviders(
        <Grid>
          <div>Grid item 1</div>
          <div>Grid item 2</div>
          <div>Grid item 3</div>
        </Grid>
      )
      
      expect(screen.getByText('Grid item 1')).toBeInTheDocument()
      expect(screen.getByText('Grid item 2')).toBeInTheDocument()
      expect(screen.getByText('Grid item 3')).toBeInTheDocument()
    })

    it('renders with custom column configuration', () => {
      renderWithProviders(
        <Grid cols={{ xs: 1, sm: 2, lg: 3 }} data-testid="custom-grid">
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Grid>
      )
      
      expect(screen.getByTestId('custom-grid')).toBeInTheDocument()
    })

    it('renders with custom gap', () => {
      renderWithProviders(
        <Grid gap={6} data-testid="custom-gap-grid">
          <div>Item 1</div>
          <div>Item 2</div>
        </Grid>
      )
      
      expect(screen.getByTestId('custom-gap-grid')).toBeInTheDocument()
    })
  })

  describe('Show', () => {
    it('renders children', () => {
      renderWithProviders(
        <Show>
          <div>Show content</div>
        </Show>
      )
      
      expect(screen.getByText('Show content')).toBeInTheDocument()
    })

    it('renders with breakpoint props', () => {
      renderWithProviders(
        <>
          <Show above="md">
            <div>Show above medium</div>
          </Show>
          <Show below="lg">
            <div>Show below large</div>
          </Show>
          <Show only="sm">
            <div>Show only small</div>
          </Show>
        </>
      )
      
      expect(screen.getByText('Show above medium')).toBeInTheDocument()
      expect(screen.getByText('Show below large')).toBeInTheDocument()
      expect(screen.getByText('Show only small')).toBeInTheDocument()
    })
  })

  describe('Hide', () => {
    it('renders children by default', () => {
      renderWithProviders(
        <Hide>
          <div>Hide content</div>
        </Hide>
      )
      
      expect(screen.getByText('Hide content')).toBeInTheDocument()
    })

    it('renders with breakpoint props', () => {
      renderWithProviders(
        <>
          <Hide above="md">
            <div>Hide above medium</div>
          </Hide>
          <Hide below="lg">
            <div>Hide below large</div>
          </Hide>
          <Hide only="sm">
            <div>Hide only small</div>
          </Hide>
        </>
      )
      
      expect(screen.getByText('Hide above medium')).toBeInTheDocument()
      expect(screen.getByText('Hide below large')).toBeInTheDocument()
      expect(screen.getByText('Hide only small')).toBeInTheDocument()
    })
  })

  describe('Spacing', () => {
    it('renders children with spacing', () => {
      renderWithProviders(
        <Spacing p={4} m={2}>
          <div>Spaced content</div>
        </Spacing>
      )
      
      expect(screen.getByText('Spaced content')).toBeInTheDocument()
    })

    it('renders with responsive spacing', () => {
      renderWithProviders(
        <Spacing p={{ xs: 2, md: 4, lg: 6 }} data-testid="responsive-spacing">
          <div>Responsive spacing</div>
        </Spacing>
      )
      
      expect(screen.getByTestId('responsive-spacing')).toBeInTheDocument()
      expect(screen.getByText('Responsive spacing')).toBeInTheDocument()
    })
  })

  describe('AspectRatio', () => {
    it('renders children with aspect ratio', () => {
      renderWithProviders(
        <AspectRatio ratio={16/9}>
          <div>Aspect ratio content</div>
        </AspectRatio>
      )
      
      expect(screen.getByText('Aspect ratio content')).toBeInTheDocument()
    })

    it('renders with custom aspect ratio', () => {
      renderWithProviders(
        <AspectRatio ratio={1} data-testid="square-aspect">
          <div>Square content</div>
        </AspectRatio>
      )
      
      expect(screen.getByTestId('square-aspect')).toBeInTheDocument()
      expect(screen.getByText('Square content')).toBeInTheDocument()
    })

    it('renders with default aspect ratio', () => {
      renderWithProviders(
        <AspectRatio data-testid="default-aspect">
          <div>Default aspect content</div>
        </AspectRatio>
      )
      
      expect(screen.getByTestId('default-aspect')).toBeInTheDocument()
      expect(screen.getByText('Default aspect content')).toBeInTheDocument()
    })
  })
})