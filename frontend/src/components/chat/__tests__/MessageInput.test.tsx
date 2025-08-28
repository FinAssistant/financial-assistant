import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../../tests/setupTests'
import MessageInput from '../MessageInput'

const defaultConversationState = {
  conversation: {
    messages: [],
    currentSessionId: null,
    isStreaming: false,
    streamingMessageId: null,
    error: null
  }
}

describe('MessageInput Component', () => {
  const mockOnSendMessage = jest.fn()

  beforeEach(() => {
    mockOnSendMessage.mockClear()
  })

  it('renders input field with placeholder', () => {
    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      { preloadedState: defaultConversationState }
    )

    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
  })

  it('renders custom placeholder', () => {
    renderWithProviders(
      <MessageInput
        onSendMessage={mockOnSendMessage}
        placeholder="Custom placeholder"
      />,
      { preloadedState: defaultConversationState }
    )

    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument()
  })

  it('sends message when form is submitted', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')
    const sendButton = screen.getByRole('button', { name: 'Send' })

    // Initially, send button should be disabled
    expect(sendButton).toBeDisabled()

    // Type message
    await user.type(input, 'Hello, AI!')

    // Send button should now be enabled
    expect(sendButton).not.toBeDisabled()

    // Click send button
    await user.click(sendButton)

    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello, AI!')
    expect(input).toHaveValue('')
  })

  it('sends message on Enter key press', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')

    await user.type(input, 'Hello via Enter!')
    await user.keyboard('{Enter}')

    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello via Enter!')
    expect(input).toHaveValue('')
  })

  it('does not send message on Shift+Enter', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')

    await user.type(input, 'Line 1')
    await user.keyboard('{Shift>}{Enter}{/Shift}')
    await user.type(input, 'Line 2')

    expect(mockOnSendMessage).not.toHaveBeenCalled()
    expect(input).toHaveValue('Line 1\nLine 2')
  })

  it('trims whitespace from messages', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')

    await user.type(input, '  Hello with spaces  ')
    await user.keyboard('{Enter}')

    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello with spaces')
  })

  it('does not send empty messages', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')
    const sendButton = screen.getByRole('button', { name: 'Send' })

    // Try sending empty message
    await user.click(sendButton)
    expect(mockOnSendMessage).not.toHaveBeenCalled()

    // Try sending whitespace only
    await user.type(input, '   ')
    await user.click(sendButton)
    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('respects character limit', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} maxLength={10} />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')

    await user.type(input, 'Short')
    expect(screen.getByText('5')).toBeInTheDocument() // 5 characters remaining

    // Try to type more, but maxLength attribute will prevent it
    await user.type(input, ' more text')

    // Should still show remaining characters (HTML maxlength prevents going over)
    expect(screen.getByText('0')).toBeInTheDocument()

    // Send button should be disabled when at limit
    const sendButton = screen.getByRole('button', { name: 'Send' })
    expect(sendButton).toBeDisabled()
  })

  it('disables input when disabled prop is true', () => {
    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} disabled />,
      { preloadedState: defaultConversationState }
    )

    const input = screen.getByRole('textbox')
    const sendButton = screen.getByRole('button', { name: 'Send' })

    expect(input).toBeDisabled()
    expect(sendButton).toBeDisabled()
  })

  it('shows streaming placeholder when streaming', () => {
    renderWithProviders(
      <MessageInput onSendMessage={mockOnSendMessage} />,
      {
        conversation: {
          messages: [],
          currentSessionId: null,
          isStreaming: true,
          streamingMessageId: null,
          error: null
        }
      }
    )

    expect(screen.getByPlaceholderText('AI is responding...')).toBeInTheDocument()
  })
})