import React, { useState, useRef, useEffect } from 'react'
import { useSelector } from 'react-redux'
import { selectIsStreaming } from '../../../store/slices/conversationSlice'
import {
  MessageInputContainer,
  InputWrapper,
  TextArea,
  SendButton,
  CharacterCount,
  InputActions
} from './styles'

interface MessageInputProps {
  onSendMessage: (message: string) => void
  placeholder?: string
  maxLength?: number
  disabled?: boolean
  className?: string
}

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  placeholder = "Type your message...",
  maxLength = 2000,
  disabled = false,
  className
}) => {
  const [message, setMessage] = useState('')
  const isStreaming = useSelector(selectIsStreaming)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const isDisabled = disabled || isStreaming
  const remainingChars = maxLength - message.length
  const isOverLimit = remainingChars <= 0
  const canSend = message.trim().length > 0 && !isOverLimit && !isDisabled

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (canSend) {
      onSendMessage(message.trim())
      setMessage('')

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)

    // Auto-resize textarea
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }

  // Focus input when not streaming
  useEffect(() => {
    if (!isStreaming && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isStreaming])

  return (
    <MessageInputContainer className={className}>
      <form onSubmit={handleSubmit}>
        <InputWrapper>
          <TextArea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? 'AI is responding...' : placeholder}
            disabled={isDisabled}
            maxLength={maxLength}
            rows={1}
            data-testid="message-input"
            role="textbox"
            aria-label="Type your message to the AI assistant"
            aria-describedby={maxLength ? "char-count" : undefined}
            aria-multiline="true"
            autoComplete="off"
          />
          <InputActions>
            {maxLength && (
              <CharacterCount 
                isOverLimit={isOverLimit}
                id="char-count"
                aria-live="polite"
                aria-label={`${remainingChars} characters remaining`}>
                {remainingChars}
              </CharacterCount>
            )}
            <SendButton
              type="submit"
              disabled={!canSend}
              size="sm"
              variant="primary"
              data-testid="send-button"
              aria-label={canSend ? "Send message to AI assistant" : "Cannot send empty message"}>
              Send
            </SendButton>
          </InputActions>
        </InputWrapper>
      </form>
    </MessageInputContainer>
  )
}

export default MessageInput