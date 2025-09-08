import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface ConversationState {
  currentSessionId: string | null
  isLoading: boolean
}

const initialState: ConversationState = {
  currentSessionId: null,
  isLoading: false,
}

const conversationSlice = createSlice({
  name: 'conversation',
  initialState,
  reducers: {
    setCurrentSessionId: (state, action: PayloadAction<string>) => {
      state.currentSessionId = action.payload
    },
    clearCurrentSessionId: (state) => {
      state.currentSessionId = null
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const { setCurrentSessionId, clearCurrentSessionId, setLoading } = conversationSlice.actions
export default conversationSlice.reducer

// Selectors
export const selectCurrentSessionId = (state: { conversation: ConversationState }) => state.conversation.currentSessionId
export const selectConversationLoading = (state: { conversation: ConversationState }) => state.conversation.isLoading