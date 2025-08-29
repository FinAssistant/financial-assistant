import React, { useEffect, useRef } from 'react'
import { useSelector } from 'react-redux'
import { selectMessages, selectIsStreaming } from '../../../store/slices/conversationSlice'
import { ConversationResponse } from '../../../store/api/apiSlice'
import {
  MessageListContainer,
  MessageContainer,
  MessageBubble,
  UserMessage,
  AssistantMessage,
  MessageMeta,
  MessageTime,
  AgentLabel,
  StreamingIndicator
} from './styles'

interface MessageListProps {
  className?: string
}

const MessageList: React.FC<MessageListProps> = ({ className }) => {
  const messages = useSelector(selectMessages)
  const isStreaming = useSelector(selectIsStreaming)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  const renderMessage = (message: ConversationResponse) => {
    const isUser = message.role === 'user'

    return (
      <MessageContainer 
        key={message.id} 
        $isUser={isUser}
        role="article"
        aria-label={`Message from ${isUser ? 'you' : message.agent}`}>
        <MessageBubble>
          {isUser ? (
            <UserMessage data-testid="user-message">{message.content}</UserMessage>
          ) : (
            <AssistantMessage data-testid="assistant-message">{message.content}</AssistantMessage>
          )}
          <MessageMeta>
            {!isUser && <AgentLabel aria-label={`Agent: ${message.agent}`}>{message.agent}</AgentLabel>}
            <MessageTime aria-label={`Sent at ${formatTime(message.created_at)}`}>{formatTime(message.created_at)}</MessageTime>
          </MessageMeta>
        </MessageBubble>
      </MessageContainer>
    )
  }

  return (
    <MessageListContainer 
      ref={containerRef}
      className={className} 
      data-testid="message-list-container"
      role="log"
      aria-live="polite"
      aria-label="Conversation messages">
      {messages.map(renderMessage)}
      {isStreaming && (
        <MessageContainer $isUser={false}>
          <MessageBubble>
            <AssistantMessage aria-live="polite" aria-label="AI assistant is typing">
              <StreamingIndicator>
                <span />
                <span />
                <span />
              </StreamingIndicator>
            </AssistantMessage>
          </MessageBubble>
        </MessageContainer>
      )}
      <div ref={messagesEndRef} aria-hidden="true" />
    </MessageListContainer>
  )
}

export default MessageList