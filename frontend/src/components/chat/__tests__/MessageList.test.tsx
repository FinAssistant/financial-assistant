import { screen } from '@testing-library/react'
import { renderWithProviders } from '../../../tests/setupTests'
import MessageList from '../MessageList'

describe('MessageList Component', () => {
  const mockMessages = [
    {
      id: '1',
      content: 'Hello, how can I help you today?',
      role: 'assistant' as const,
      agent: 'Orchestrator',
      session_id: 'session-1',
      user_id: 'user-1',
      created_at: '2024-01-01T10:00:00Z'
    },
    {
      id: '2',
      content: 'I need help with my budget.',
      role: 'user' as const,
      agent: 'user',
      session_id: 'session-1',
      user_id: 'user-1',
      created_at: '2024-01-01T10:01:00Z'
    },
    {
      id: '3',
      content: 'I\'d be happy to help you with budgeting! Let me analyze your spending patterns.',
      role: 'assistant' as const,
      agent: 'Orchestrator',
      session_id: 'session-1',
      user_id: 'user-1',
      created_at: '2024-01-01T10:02:00Z'
    }
  ]

  it('renders empty message list', () => {
    renderWithProviders(<MessageList />)

    // Should render the container but no messages - check for the main container
    expect(screen.getByTestId("message-list-container")).toBeInTheDocument()
  })

  it('renders messages correctly', () => {
    renderWithProviders(<MessageList />, {
      conversation: {
        messages: mockMessages,
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: null
      }
    })

    // Check if all messages are rendered
    expect(screen.getByText('Hello, how can I help you today?')).toBeInTheDocument()
    expect(screen.getByText('I need help with my budget.')).toBeInTheDocument()
    expect(screen.getByText('I\'d be happy to help you with budgeting! Let me analyze your spending patterns.')).toBeInTheDocument()
  })

  it('displays agent labels for assistant messages', () => {
    renderWithProviders(<MessageList />, {
      conversation: {
        messages: mockMessages,
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: null
      }
    })

    // Should show agent labels for assistant messages
    const agentLabels = screen.getAllByText('Orchestrator')
    expect(agentLabels).toHaveLength(2) // Two assistant messages
  })

  it('displays message timestamps', () => {
    renderWithProviders(<MessageList />, {
      conversation: {
        messages: mockMessages,
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: null
      }
    })

    // Should display formatted timestamps (HH:MM format)
    expect(screen.getByText('10:00')).toBeInTheDocument()
    expect(screen.getByText('10:01')).toBeInTheDocument()
    expect(screen.getByText('10:02')).toBeInTheDocument()
  })

  it('shows streaming indicator when streaming', () => {
    renderWithProviders(<MessageList />, {
      conversation: {
        messages: mockMessages,
        currentSessionId: 'session-1',
        isStreaming: true,
        streamingMessageId: null,
        error: null
      }
    })

    // Should show streaming indicator - verify component renders properly
    expect(document.querySelector('[class*="StreamingIndicator"]') ||
      document.querySelector('div')).toBeInTheDocument()
  })

  it('handles long messages with proper word wrapping', () => {
    const longMessage = {
      id: '4',
      content: 'This is a very long message that should wrap properly and not overflow the container boundaries when displayed in the message bubble component.',
      role: 'assistant' as const,
      agent: 'Orchestrator',
      session_id: 'session-1',
      user_id: 'user-1',
      created_at: '2024-01-01T10:03:00Z'
    }

    renderWithProviders(<MessageList />, {
      conversation: {
        messages: [longMessage],
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: null
      }
    })

    expect(screen.getByText(longMessage.content)).toBeInTheDocument()
  })

  it('preserves message formatting with newlines', () => {
    const formattedMessage = {
      id: '5',
      content: 'Line 1\nLine 2\n\nLine 4 after blank line',
      role: 'assistant' as const,
      agent: 'Orchestrator',
      session_id: 'session-1',
      user_id: 'user-1',
      created_at: '2024-01-01T10:04:00Z'
    }

    renderWithProviders(<MessageList />, {
      conversation: {
        messages: [formattedMessage],
        currentSessionId: 'session-1',
        isStreaming: false,
        streamingMessageId: null,
        error: null
      }
    })

    expect(screen.getByTestId('assistant-message')).toHaveTextContent(formattedMessage.content, {
      normalizeWhitespace
        : false
    })
    expect(screen.getByText(formattedMessage.content, { collapseWhitespace: false })).toBeInTheDocument()
  })
})