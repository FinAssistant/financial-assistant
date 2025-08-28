import { screen } from '@testing-library/react'
import { renderWithProviders } from '../../../tests/setupTests'
import { Heading, Text, Caption, Overline, Currency, Percentage } from '../Typography'

describe('Typography Components', () => {
  describe('Heading', () => {
    it('renders heading with default props', () => {
      renderWithProviders(<Heading>Test Heading</Heading>)
      
      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
      expect(heading).toHaveTextContent('Test Heading')
    })

    it('renders different heading levels', () => {
      renderWithProviders(<Heading level={1}>H1 Heading</Heading>)
      
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toBeInTheDocument()
      expect(heading.tagName).toBe('H1')
    })

    it('applies color variants correctly', () => {
      renderWithProviders(<Heading color="secondary">Secondary Heading</Heading>)
      
      const heading = screen.getByRole('heading')
      expect(heading).toBeInTheDocument()
    })
  })

  describe('Text', () => {
    it('renders text with default props', () => {
      renderWithProviders(<Text>Test text content</Text>)
      
      expect(screen.getByText('Test text content')).toBeInTheDocument()
    })

    it('renders different text sizes', () => {
      renderWithProviders(<Text size="lg">Large text</Text>)
      
      expect(screen.getByText('Large text')).toBeInTheDocument()
    })

    it('applies text alignment', () => {
      renderWithProviders(<Text align="center">Centered text</Text>)
      
      expect(screen.getByText('Centered text')).toBeInTheDocument()
    })
  })

  describe('Caption', () => {
    it('renders caption text', () => {
      renderWithProviders(<Caption>Caption text</Caption>)
      
      expect(screen.getByText('Caption text')).toBeInTheDocument()
    })
  })

  describe('Overline', () => {
    it('renders overline text', () => {
      renderWithProviders(<Overline>Overline text</Overline>)
      
      expect(screen.getByText('Overline text')).toBeInTheDocument()
    })
  })

  describe('Currency', () => {
    it('formats positive currency value', () => {
      renderWithProviders(<Currency value={1234.56} />)
      
      expect(screen.getByText('$1,234.56')).toBeInTheDocument()
    })

    it('formats negative currency value', () => {
      renderWithProviders(<Currency value={-1234.56} />)
      
      expect(screen.getByText('-$1,234.56')).toBeInTheDocument()
    })

    it('shows sign for positive values when requested', () => {
      renderWithProviders(<Currency value={1234.56} showSign />)
      
      expect(screen.getByText('+$1,234.56')).toBeInTheDocument()
    })

    it('formats different currencies', () => {
      renderWithProviders(<Currency value={1234.56} currency="EUR" />)
      
      expect(screen.getByText('€1,234.56')).toBeInTheDocument()
    })
  })

  describe('Percentage', () => {
    it('formats positive percentage', () => {
      renderWithProviders(<Percentage value={12.34} />)
      
      expect(screen.getByText('+12.34%')).toBeInTheDocument()
    })

    it('formats negative percentage', () => {
      renderWithProviders(<Percentage value={-12.34} />)
      
      expect(screen.getByText('-12.34%')).toBeInTheDocument()
    })

    it('formats percentage without sign when requested', () => {
      renderWithProviders(<Percentage value={12.34} showSign={false} />)
      
      expect(screen.getByText('12.34%')).toBeInTheDocument()
    })

    it('formats percentage with custom decimals', () => {
      renderWithProviders(<Percentage value={12.345} decimals={1} />)
      
      expect(screen.getByText('+12.3%')).toBeInTheDocument()
    })
  })
})