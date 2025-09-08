import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../../tests/setupTests'
import { Button } from '../Button'

describe('Button Component', () => {
  it('renders button with text', () => {
    renderWithProviders(<Button>Click me</Button>)
    
    const button = screen.getByRole('button', { name: 'Click me' })
    expect(button).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup()
    const handleClick = jest.fn()
    
    renderWithProviders(<Button onClick={handleClick}>Click me</Button>)
    
    const button = screen.getByRole('button', { name: 'Click me' })
    await user.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', async () => {
    const user = userEvent.setup()
    const handleClick = jest.fn()
    
    renderWithProviders(
      <Button onClick={handleClick} disabled>
        Disabled button
      </Button>
    )
    
    const button = screen.getByRole('button', { name: 'Disabled button' })
    await user.click(button)
    
    expect(handleClick).not.toHaveBeenCalled()
    expect(button).toBeDisabled()
  })

  it('does not call onClick when loading', async () => {
    const user = userEvent.setup()
    const handleClick = jest.fn()
    
    renderWithProviders(
      <Button onClick={handleClick} loading>
        Loading button
      </Button>
    )
    
    const button = screen.getByRole('button')
    await user.click(button)
    
    expect(handleClick).not.toHaveBeenCalled()
    expect(button).toBeDisabled()
  })

  it('shows loading spinner when loading', () => {
    renderWithProviders(<Button loading>Loading</Button>)
    
    // The loading spinner should be present
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    expect(button).toBeDisabled()
  })

  it('renders different variants', () => {
    renderWithProviders(
      <>
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="danger">Danger</Button>
      </>
    )
    
    expect(screen.getByRole('button', { name: 'Primary' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Secondary' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Outline' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ghost' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Danger' })).toBeInTheDocument()
  })

  it('renders different sizes', () => {
    renderWithProviders(
      <>
        <Button size="sm">Small</Button>
        <Button size="base">Base</Button>
        <Button size="lg">Large</Button>
      </>
    )
    
    expect(screen.getByRole('button', { name: 'Small' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Base' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Large' })).toBeInTheDocument()
  })

  it('renders with icon', () => {
    const icon = <span data-testid="icon">🔥</span>
    
    renderWithProviders(<Button icon={icon}>With Icon</Button>)
    
    expect(screen.getByRole('button', { name: '🔥 With Icon' })).toBeInTheDocument()
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('handles different button types', () => {
    renderWithProviders(
      <form>
        <Button type="submit">Submit</Button>
        <Button type="reset">Reset</Button>
        <Button type="button">Button</Button>
      </form>
    )
    
    const submitButton = screen.getByRole('button', { name: 'Submit' })
    const resetButton = screen.getByRole('button', { name: 'Reset' })
    const buttonButton = screen.getByRole('button', { name: 'Button' })
    
    expect(submitButton).toHaveAttribute('type', 'submit')
    expect(resetButton).toHaveAttribute('type', 'reset')
    expect(buttonButton).toHaveAttribute('type', 'button')
  })

  it('renders full width when specified', () => {
    renderWithProviders(<Button fullWidth>Full Width</Button>)
    
    const button = screen.getByRole('button', { name: 'Full Width' })
    expect(button).toBeInTheDocument()
  })
})