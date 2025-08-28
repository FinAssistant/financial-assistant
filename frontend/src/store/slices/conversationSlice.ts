import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { RootState } from '../index'
import type { ConversationResponse } from '../api/apiSlice'

interface ConversationState {
  messages: ConversationResponse[]
  currentSessionId: string | null
  isStreaming: boolean
  streamingMessageId: string | null
  error: string | null
}

const initialState: ConversationState = {
  messages: [],
  currentSessionId: null,
  isStreaming: false,
  streamingMessageId: null,
  error: null,
}

const conversationSlice = createSlice({
  name: 'conversation',
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<ConversationResponse>) => {
      state.messages.push(action.payload)
      if (action.payload.session_id) {
        state.currentSessionId = action.payload.session_id
      }
    },
    setStreaming: (state, action: PayloadAction<{ isStreaming: boolean; messageId?: string }>) => {
      state.isStreaming = action.payload.isStreaming
      state.streamingMessageId = action.payload.messageId || null
    },
    updateStreamingMessage: (state, action: PayloadAction<{ messageId: string; content: string }>) => {
      const message = state.messages.find(m => m.id === action.payload.messageId)
      if (message) {
        message.content = action.payload.content
      }
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearMessages: (state) => {
      state.messages = []
      state.currentSessionId = null
      state.isStreaming = false
      state.streamingMessageId = null
      state.error = null
    },
    setSessionId: (state, action: PayloadAction<string>) => {
      state.currentSessionId = action.payload
    },
  },
})

export const {
  addMessage,
  setStreaming,
  updateStreamingMessage,
  setError,
  clearMessages,
  setSessionId,
} = conversationSlice.actions

// Selectors
export const selectMessages = (state: RootState) => state.conversation.messages
export const selectCurrentSessionId = (state: RootState) => state.conversation.currentSessionId
export const selectIsStreaming = (state: RootState) => state.conversation.isStreaming
export const selectStreamingMessageId = (state: RootState) => state.conversation.streamingMessageId
export const selectConversationError = (state: RootState) => state.conversation.error

export default conversationSlice.reducer