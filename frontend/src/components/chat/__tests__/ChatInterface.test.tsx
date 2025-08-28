import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../../tests/setupTests'
import ChatInterface from '../ChatInterface'

// Mock the RTK Query hook with proper typing
const mockSendMessage = jest.fn()
const mockIsLoading = jest.fn(() => false)

jest.mock('../../../store/api/apiSlice', () => ({
  ...jest.requireActual('../../../store/api/apiSlice'),
  useSendMessageNonStreamingConversationMessagePostMutation: () => [
    mockSendMessage,
    { isLoading: mockIsLoading() }
  ]
}))

const mockResponse = {
  id: 'response-1',
  content: 'Mock AI response',
  role: 'assistant' as const,
  agent: 'Orchestrator',
  session_id: 'session-1',
  user_id: 'user-1',
  created_at: new Date().toISOString()
}

describe('ChatInterface Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default successful mock implementation
    mockSendMessage.mockImplementation(() => ({
      unwrap: () => Promise.resolve(mockResponse)
    }))
  })

  it('renders with default title', () => {
    renderWithProviders(<ChatInterface />)

    expect(screen.getByText('AI Assistant')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask me anything about your finances...')).toBeInTheDocument()
  })

  it('renders with custom title', () => {
    renderWithProviders(<ChatInterface title="Custom Assistant" />)

    expect(screen.getByText('Custom Assistant')).toBeInTheDocument()
  })

  it('generates session ID on mount when none exists', () => {
    renderWithProviders(<ChatInterface />)

    // Component should render without errors even without initial session ID
    expect(screen.getByText('AI Assistant')).toBeInTheDocument()
  })

  it('sends message and updates conversation', async () => {
    const user = userEvent.setup()

    renderWithProviders(<ChatInterface />)

    const input = screen.getByRole('textbox')
    const sendButton = screen.getByRole('button', { name: 'Send' })

    // Type and send a message
    await user.type(input, 'Hello, assistant!')
    await user.click(sendButton)

    // Should show the user message immediately
    await waitFor(() => {
      expect(screen.getByText('Hello, assistant!')).toBeInTheDocument()
    })

    // Should eventually show the AI response
    await waitFor(() => {
      expect(screen.getByText('Mock AI response')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays error message when API call fails', async () => {
    const user = userEvent.setup()

    // Mock failed API call
    mockSendMessage.mockImplementation(() => ({
      unwrap: () => Promise.reject({
        data: { detail: 'API Error occurred' }
      })
    }))

    renderWithProviders(<ChatInterface />)

    const input = screen.getByRole('textbox')

    await user.type(input, 'This will fail')
    await user.keyboard('{Enter}')

    // Should show error message (uses the detail from the mock)
    await waitFor(() => {
      expect(screen.getByText('API Error occurred')).toBeInTheDocument()
    })
  })

  it('clears error message when clicked', async () => {
    const user = userEvent.setup()

    renderWithProviders(<ChatInterface />, {
      conversation: {
        messages: [],
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: 'Test error message'
      }
    })

    const errorMessage = screen.getByText('Test error message')
    expect(errorMessage).toBeInTheDocument()

    // Click to dismiss error
    await user.click(errorMessage)

    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText('Test error message')).not.toBeInTheDocument()
    })
  })

  it('disables input when sending message', async () => {
    // Mock loading state
    mockIsLoading.mockReturnValue(true)

    renderWithProviders(<ChatInterface />)

    const input = screen.getByRole('textbox')
    const sendButton = screen.getByRole('button', { name: 'Send' })

    expect(input).toBeDisabled()
    expect(sendButton).toBeDisabled()
  })

  it('maintains existing messages when sending new message', async () => {
    const user = userEvent.setup()

    // Reset loading state for this test
    mockIsLoading.mockReturnValue(false)

    const existingMessages = [
      {
        id: '1',
        content: 'Previous message',
        role: 'user' as const,
        agent: 'user',
        session_id: 'session-1',
        user_id: 'user-1',
        created_at: '2024-01-01T10:00:00Z'
      }
    ]

    renderWithProviders(<ChatInterface />, {
      conversation: {
        messages: existingMessages,
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: null
      }
    })

    // Should show existing message
    expect(screen.getByText('Previous message')).toBeInTheDocument()

    const input = screen.getByRole('textbox')

    // Send new message
    await user.type(input, 'New message')
    await user.keyboard('{Enter}')

    // Should show both user messages and AI response
    await waitFor(() => {
      expect(screen.getByText('Previous message')).toBeInTheDocument()
      expect(screen.getByText('New message')).toBeInTheDocument()
      expect(screen.getByText('Mock AI response')).toBeInTheDocument()
    })
  })
})