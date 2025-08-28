import conversationReducer, {
  addMessage,
  setStreaming,
  updateStreamingMessage,
  setError,
  clearMessages,
  setSessionId,
  selectMessages,
  selectCurrentSessionId,
  selectIsStreaming,
  selectStreamingMessageId,
  selectConversationError,
} from '../slices/conversationSlice'
import type { ConversationResponse } from '../api/apiSlice'
import type { RootState } from '../index'

const initialState = {
  messages: [],
  currentSessionId: null,
  isStreaming: false,
  streamingMessageId: null,
  error: null,
}

const mockMessage: ConversationResponse = {
  id: '123',
  content: 'Hello, how can I help you?',
  role: 'assistant',
  agent: 'orchestrator',
  session_id: 'session-123',
  user_id: 'user-456',
  created_at: '2023-01-01T00:00:00Z',
}

describe('conversationSlice', () => {
  it('should return the initial state', () => {
    expect(conversationReducer(undefined, { type: 'unknown' })).toEqual(initialState)
  })

  it('should handle addMessage', () => {
    const actual = conversationReducer(initialState, addMessage(mockMessage))
    expect(actual.messages).toHaveLength(1)
    expect(actual.messages[0]).toEqual(mockMessage)
    expect(actual.currentSessionId).toBe('session-123')
  })

  it('should handle setStreaming', () => {
    const actual = conversationReducer(initialState, setStreaming({ isStreaming: true, messageId: '456' }))
    expect(actual.isStreaming).toBe(true)
    expect(actual.streamingMessageId).toBe('456')
  })

  it('should handle setStreaming without messageId', () => {
    const actual = conversationReducer(initialState, setStreaming({ isStreaming: false }))
    expect(actual.isStreaming).toBe(false)
    expect(actual.streamingMessageId).toBeNull()
  })

  it('should handle updateStreamingMessage', () => {
    const stateWithMessage = {
      ...initialState,
      messages: [mockMessage],
    }
    const actual = conversationReducer(
      stateWithMessage,
      updateStreamingMessage({ messageId: '123', content: 'Updated content' })
    )
    expect(actual.messages[0].content).toBe('Updated content')
  })

  it('should handle updateStreamingMessage for non-existent message', () => {
    const actual = conversationReducer(
      initialState,
      updateStreamingMessage({ messageId: 'non-existent', content: 'Updated content' })
    )
    expect(actual.messages).toHaveLength(0)
  })

  it('should handle setError', () => {
    const actual = conversationReducer(initialState, setError('Something went wrong'))
    expect(actual.error).toBe('Something went wrong')
  })

  it('should handle clearMessages', () => {
    const stateWithData = {
      messages: [mockMessage],
      currentSessionId: 'session-123',
      isStreaming: true,
      streamingMessageId: '456',
      error: 'Some error',
    }
    const actual = conversationReducer(stateWithData, clearMessages())
    expect(actual).toEqual(initialState)
  })

  it('should handle setSessionId', () => {
    const actual = conversationReducer(initialState, setSessionId('new-session-id'))
    expect(actual.currentSessionId).toBe('new-session-id')
  })
})

describe('conversation selectors', () => {
  const mockState = {
    conversation: {
      messages: [mockMessage],
      currentSessionId: 'session-123',
      isStreaming: true,
      streamingMessageId: '456',
      error: 'Test error',
    },
  } as RootState

  it('should select messages', () => {
    expect(selectMessages(mockState)).toEqual([mockMessage])
  })

  it('should select current session ID', () => {
    expect(selectCurrentSessionId(mockState)).toBe('session-123')
  })

  it('should select isStreaming', () => {
    expect(selectIsStreaming(mockState)).toBe(true)
  })

  it('should select streaming message ID', () => {
    expect(selectStreamingMessageId(mockState)).toBe('456')
  })

  it('should select conversation error', () => {
    expect(selectConversationError(mockState)).toBe('Test error')
  })
})