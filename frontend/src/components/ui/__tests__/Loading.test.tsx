import { screen } from '@testing-library/react'
import { renderWithProviders } from '../../../tests/setupTests'
import { 
  Spinner, 
  LoadingDots, 
  LoadingWave, 
  Skeleton, 
  PageLoading, 
  OverlayLoading 
} from '../Loading'

describe('Loading Components', () => {
  describe('Spinner', () => {
    it('renders spinner with default props', () => {
      renderWithProviders(<Spinner />)
      
      const spinner = screen.getByRole('status', { name: 'Loading' })
      expect(spinner).toBeInTheDocument()
    })

    it('renders different sizes', () => {
      renderWithProviders(
        <>
          <Spinner size="sm" data-testid="small-spinner" />
          <Spinner size="base" data-testid="base-spinner" />
          <Spinner size="lg" data-testid="large-spinner" />
          <Spinner size="xl" data-testid="xl-spinner" />
        </>
      )
      
      expect(screen.getByTestId('small-spinner')).toBeInTheDocument()
      expect(screen.getByTestId('base-spinner')).toBeInTheDocument()
      expect(screen.getByTestId('large-spinner')).toBeInTheDocument()
      expect(screen.getByTestId('xl-spinner')).toBeInTheDocument()
    })

    it('renders different colors', () => {
      renderWithProviders(
        <>
          <Spinner color="primary" data-testid="primary-spinner" />
          <Spinner color="secondary" data-testid="secondary-spinner" />
          <Spinner color="white" data-testid="white-spinner" />
        </>
      )
      
      expect(screen.getByTestId('primary-spinner')).toBeInTheDocument()
      expect(screen.getByTestId('secondary-spinner')).toBeInTheDocument()
      expect(screen.getByTestId('white-spinner')).toBeInTheDocument()
    })
  })

  describe('LoadingDots', () => {
    it('renders loading dots', () => {
      renderWithProviders(<LoadingDots />)
      
      const dots = screen.getByRole('status', { name: 'Loading' })
      expect(dots).toBeInTheDocument()
    })

    it('renders different sizes', () => {
      renderWithProviders(
        <>
          <LoadingDots size="sm" data-testid="small-dots" />
          <LoadingDots size="base" data-testid="base-dots" />
          <LoadingDots size="lg" data-testid="large-dots" />
        </>
      )
      
      expect(screen.getByTestId('small-dots')).toBeInTheDocument()
      expect(screen.getByTestId('base-dots')).toBeInTheDocument()
      expect(screen.getByTestId('large-dots')).toBeInTheDocument()
    })
  })

  describe('LoadingWave', () => {
    it('renders loading wave', () => {
      renderWithProviders(<LoadingWave />)
      
      const wave = screen.getByRole('status', { name: 'Loading' })
      expect(wave).toBeInTheDocument()
    })

    it('renders different sizes', () => {
      renderWithProviders(
        <>
          <LoadingWave size="sm" data-testid="small-wave" />
          <LoadingWave size="base" data-testid="base-wave" />
          <LoadingWave size="lg" data-testid="large-wave" />
        </>
      )
      
      expect(screen.getByTestId('small-wave')).toBeInTheDocument()
      expect(screen.getByTestId('base-wave')).toBeInTheDocument()
      expect(screen.getByTestId('large-wave')).toBeInTheDocument()
    })
  })

  describe('Skeleton', () => {
    it('renders skeleton with default props', () => {
      renderWithProviders(<Skeleton />)
      
      const skeleton = screen.getByRole('status', { name: 'Loading content' })
      expect(skeleton).toBeInTheDocument()
    })

    it('renders different variants', () => {
      renderWithProviders(
        <>
          <Skeleton variant="text" data-testid="text-skeleton" />
          <Skeleton variant="circular" data-testid="circular-skeleton" />
          <Skeleton variant="rectangular" data-testid="rectangular-skeleton" />
        </>
      )
      
      expect(screen.getByTestId('text-skeleton')).toBeInTheDocument()
      expect(screen.getByTestId('circular-skeleton')).toBeInTheDocument()
      expect(screen.getByTestId('rectangular-skeleton')).toBeInTheDocument()
    })

    it('accepts custom width and height', () => {
      renderWithProviders(
        <Skeleton width="200px" height="100px" data-testid="custom-skeleton" />
      )
      
      expect(screen.getByTestId('custom-skeleton')).toBeInTheDocument()
    })
  })

  describe('PageLoading', () => {
    it('renders page loading with default message', () => {
      renderWithProviders(<PageLoading />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
    })

    it('renders with custom message', () => {
      renderWithProviders(<PageLoading message="Loading your data..." />)
      
      expect(screen.getByText('Loading your data...')).toBeInTheDocument()
    })

    it('renders different sizes', () => {
      renderWithProviders(
        <>
          <PageLoading size="base" />
          <PageLoading size="lg" />
          <PageLoading size="xl" />
        </>
      )
      
      // Should render multiple spinners
      const spinners = screen.getAllByRole('status', { name: 'Loading' })
      expect(spinners).toHaveLength(3)
    })
  })

  describe('OverlayLoading', () => {
    it('renders overlay loading when visible', () => {
      renderWithProviders(<OverlayLoading isVisible={true} />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
    })

    it('does not render when not visible', () => {
      renderWithProviders(<OverlayLoading isVisible={false} />)
      
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    it('renders with custom message', () => {
      renderWithProviders(
        <OverlayLoading isVisible={true} message="Processing your request..." />
      )
      
      expect(screen.getByText('Processing your request...')).toBeInTheDocument()
    })
  })
})