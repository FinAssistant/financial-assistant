import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../../tests/setupTests'
import { Alert, InfoAlert, SuccessAlert, WarningAlert, ErrorAlert } from '../Alert'

describe('Alert Components', () => {
  describe('Alert', () => {
    it('renders alert with message', () => {
      renderWithProviders(<Alert>Test alert message</Alert>)
      
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
      expect(screen.getByText('Test alert message')).toBeInTheDocument()
    })

    it('renders different variants', () => {
      renderWithProviders(
        <>
          <Alert variant="info">Info alert</Alert>
          <Alert variant="success">Success alert</Alert>
          <Alert variant="warning">Warning alert</Alert>
          <Alert variant="error">Error alert</Alert>
        </>
      )
      
      expect(screen.getByText('Info alert')).toBeInTheDocument()
      expect(screen.getByText('Success alert')).toBeInTheDocument()
      expect(screen.getByText('Warning alert')).toBeInTheDocument()
      expect(screen.getByText('Error alert')).toBeInTheDocument()
    })

    it('renders different sizes', () => {
      renderWithProviders(
        <>
          <Alert size="sm">Small alert</Alert>
          <Alert size="base">Base alert</Alert>
          <Alert size="lg">Large alert</Alert>
        </>
      )
      
      expect(screen.getByText('Small alert')).toBeInTheDocument()
      expect(screen.getByText('Base alert')).toBeInTheDocument()
      expect(screen.getByText('Large alert')).toBeInTheDocument()
    })

    it('renders with title', () => {
      renderWithProviders(
        <Alert title="Alert Title">Alert message</Alert>
      )
      
      expect(screen.getByText('Alert Title')).toBeInTheDocument()
      expect(screen.getByText('Alert message')).toBeInTheDocument()
    })

    it('renders dismissible alert with close button', () => {
      const handleDismiss = jest.fn()
      
      renderWithProviders(
        <Alert dismissible onDismiss={handleDismiss}>
          Dismissible alert
        </Alert>
      )
      
      const closeButton = screen.getByRole('button', { name: 'Dismiss alert' })
      expect(closeButton).toBeInTheDocument()
    })

    it('calls onDismiss when close button is clicked', async () => {
      const user = userEvent.setup()
      const handleDismiss = jest.fn()
      
      renderWithProviders(
        <Alert dismissible onDismiss={handleDismiss}>
          Dismissible alert
        </Alert>
      )
      
      const closeButton = screen.getByRole('button', { name: 'Dismiss alert' })
      await user.click(closeButton)
      
      expect(handleDismiss).toHaveBeenCalledTimes(1)
    })

    it('does not render close button when not dismissible', () => {
      renderWithProviders(<Alert>Non-dismissible alert</Alert>)
      
      expect(screen.queryByRole('button', { name: 'Dismiss alert' })).not.toBeInTheDocument()
    })
  })

  describe('Specialized Alert Components', () => {
    it('renders InfoAlert', () => {
      renderWithProviders(<InfoAlert>Info message</InfoAlert>)
      
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
      expect(screen.getByText('Info message')).toBeInTheDocument()
    })

    it('renders SuccessAlert', () => {
      renderWithProviders(<SuccessAlert>Success message</SuccessAlert>)
      
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
      expect(screen.getByText('Success message')).toBeInTheDocument()
    })

    it('renders WarningAlert', () => {
      renderWithProviders(<WarningAlert>Warning message</WarningAlert>)
      
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
      expect(screen.getByText('Warning message')).toBeInTheDocument()
    })

    it('renders ErrorAlert', () => {
      renderWithProviders(<ErrorAlert>Error message</ErrorAlert>)
      
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
      expect(screen.getByText('Error message')).toBeInTheDocument()
    })

    it('specialized alerts support all base alert props', () => {
      const handleDismiss = jest.fn()
      
      renderWithProviders(
        <SuccessAlert 
          title="Success!" 
          size="lg" 
          dismissible 
          onDismiss={handleDismiss}
        >
          Operation completed successfully
        </SuccessAlert>
      )
      
      expect(screen.getByText('Success!')).toBeInTheDocument()
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Dismiss alert' })).toBeInTheDocument()
    })
  })

  it('applies custom className', () => {
    renderWithProviders(
      <Alert className="custom-alert" data-testid="custom-alert">
        Custom alert
      </Alert>
    )
    
    const alert = screen.getByTestId('custom-alert')
    expect(alert).toHaveClass('custom-alert')
  })
})