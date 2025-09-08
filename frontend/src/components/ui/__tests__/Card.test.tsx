import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../../tests/setupTests'
import { Card } from '../Card'

describe('Card Component', () => {
  it('renders card with children', () => {
    renderWithProviders(
      <Card>
        <div>Card content</div>
      </Card>
    )
    
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('renders different variants', () => {
    renderWithProviders(
      <>
        <Card variant="default" data-testid="default-card">Default</Card>
        <Card variant="outlined" data-testid="outlined-card">Outlined</Card>
        <Card variant="elevated" data-testid="elevated-card">Elevated</Card>
      </>
    )
    
    expect(screen.getByTestId('default-card')).toBeInTheDocument()
    expect(screen.getByTestId('outlined-card')).toBeInTheDocument()
    expect(screen.getByTestId('elevated-card')).toBeInTheDocument()
  })

  it('renders different sizes', () => {
    renderWithProviders(
      <>
        <Card size="sm" data-testid="small-card">Small</Card>
        <Card size="base" data-testid="base-card">Base</Card>
        <Card size="lg" data-testid="large-card">Large</Card>
      </>
    )
    
    expect(screen.getByTestId('small-card')).toBeInTheDocument()
    expect(screen.getByTestId('base-card')).toBeInTheDocument()
    expect(screen.getByTestId('large-card')).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup()
    const handleClick = jest.fn()
    
    renderWithProviders(
      <Card onClick={handleClick}>
        <div>Clickable card</div>
      </Card>
    )
    
    const card = screen.getByRole('button')
    await user.click(card)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('renders with hover effect when specified', () => {
    renderWithProviders(
      <Card hover data-testid="hover-card">
        <div>Hover card</div>
      </Card>
    )
    
    expect(screen.getByTestId('hover-card')).toBeInTheDocument()
  })

  it('renders with Card.Header, Card.Body, and Card.Footer', () => {
    renderWithProviders(
      <Card>
        <Card.Header>
          <h3>Card Title</h3>
        </Card.Header>
        <Card.Body>
          <p>Card body content</p>
        </Card.Body>
        <Card.Footer>
          <button>Action</button>
        </Card.Footer>
      </Card>
    )
    
    expect(screen.getByText('Card Title')).toBeInTheDocument()
    expect(screen.getByText('Card body content')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
  })

  it('applies custom className', () => {
    renderWithProviders(
      <Card className="custom-class" data-testid="custom-card">
        Custom card
      </Card>
    )
    
    const card = screen.getByTestId('custom-card')
    expect(card).toHaveClass('custom-class')
  })

  it('has proper accessibility attributes when clickable', () => {
    renderWithProviders(
      <Card onClick={() => {}}>
        <div>Clickable card</div>
      </Card>
    )
    
    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('tabIndex', '0')
  })
})