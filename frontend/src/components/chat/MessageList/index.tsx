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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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
      <MessageContainer key={message.id} $isUser={isUser}>
        <MessageBubble>
          {isUser ? (
            <UserMessage data-testid="user-message">{message.content}</UserMessage>
          ) : (
            <AssistantMessage data-testid="assistant-message">{message.content}</AssistantMessage>
          )}
          <MessageMeta>
            {!isUser && <AgentLabel>{message.agent}</AgentLabel>}
            <MessageTime>{formatTime(message.created_at)}</MessageTime>
          </MessageMeta>
        </MessageBubble>
      </MessageContainer>
    )
  }

  return (
    <MessageListContainer className={className} data-testid="message-list-container">
      {messages.map(renderMessage)}
      {isStreaming && (
        <MessageContainer $isUser={false}>
          <MessageBubble>
            <AssistantMessage>
              <StreamingIndicator>
                <span />
                <span />
                <span />
              </StreamingIndicator>
            </AssistantMessage>
          </MessageBubble>
        </MessageContainer>
      )}
      <div ref={messagesEndRef} />
    </MessageListContainer>
  )
}

export default MessageList