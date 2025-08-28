import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from '../../../store'
import {
  selectCurrentSessionId,
  selectConversationError,
  addMessage,
  setStreaming,
  setError,
  setSessionId
} from '../../../store/slices/conversationSlice'
import { useSendMessageNonStreamingConversationMessagePostMutation } from '../../../store/api/apiSlice'
import MessageList from '../MessageList'
import MessageInput from '../MessageInput'
import {
  ChatContainer,
  ChatHeader,
  ChatTitle,
  ErrorMessage
} from './styles'

interface ChatInterfaceProps {
  className?: string
  title?: string
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  className,
  title = "AI Assistant"
}) => {
  const dispatch = useDispatch<AppDispatch>()
  const currentSessionId = useSelector(selectCurrentSessionId)
  const conversationError = useSelector(selectConversationError)

  const [sendMessage, { isLoading: isSending }] = useSendMessageNonStreamingConversationMessagePostMutation()

  // Generate session ID on mount if none exists
  useEffect(() => {
    if (!currentSessionId) {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      dispatch(setSessionId(newSessionId))
    }
  }, [currentSessionId, dispatch])

  const handleSendMessage = async (messageText: string) => {
    console.info('Sending message:', messageText)
    if (!messageText.trim() || isSending) {
      return
    }

    try {
      // Clear any previous errors
      dispatch(setError(null))

      // Add user message to the conversation
      const userMessage = {
        id: `msg_${Date.now()}_user`,
        content: messageText,
        role: 'user' as const,
        agent: 'user',
        session_id: currentSessionId || '',
        user_id: 'current-user', // This should come from auth state
        created_at: new Date().toISOString()
      }

      dispatch(addMessage(userMessage))
      dispatch(setStreaming({ isStreaming: true }))

      // Send message to backend
      const response = await sendMessage({
        conversationRequest: {
          message: messageText,
          session_id: currentSessionId
        }
      }).unwrap()

      // Add assistant response to conversation
      dispatch(addMessage(response))

    } catch (error: unknown) {
      console.error('Failed to send message:', error)
      const errorMessage = (error as { data?: { detail?: string } })?.data?.detail || 'Failed to send message. Please try again.'
      dispatch(setError(errorMessage))
    } finally {
      dispatch(setStreaming({ isStreaming: false }))
    }
  }

  const handleClearError = () => {
    dispatch(setError(null))
  }

  return (
    <ChatContainer className={className}>
      <ChatHeader>
        <ChatTitle>{title}</ChatTitle>
      </ChatHeader>

      {conversationError && (
        <ErrorMessage onClick={handleClearError}>
          {conversationError}
          <span>Click to dismiss</span>
        </ErrorMessage>
      )}

      <MessageList />

      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isSending}
        placeholder="Ask me anything about your finances..."
      />
    </ChatContainer>
  )
}

export default ChatInterface