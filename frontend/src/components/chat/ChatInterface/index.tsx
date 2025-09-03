import React, { useEffect } from 'react'
import { MessageCircle, Send } from 'lucide-react'
import { useSelector, useDispatch } from 'react-redux'
import { 
  AssistantRuntimeProvider, 
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from '@assistant-ui/react'
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { 
  selectCurrentSessionId, 
  setCurrentSessionId 
} from '../../../store/slices/conversationSlice'
import {
  ChatContainer,
  ChatHeader,
  ChatTitle,
  StyledThreadContainer,
} from './styles'
import { DefaultChatTransport } from 'ai';

interface ChatInterfaceProps {
  className?: string
}

// Generate session ID consistent with backend pattern: f"session_{user_id}"
const generateSessionId = (userId?: string): string => {
  return userId ? `session_${userId}` : `session_guest_${Date.now()}`
}

// Simple message components
const UserMessage = () => (
  <MessagePrimitive.Root>
    <MessagePrimitive.Content />
  </MessagePrimitive.Root>
)

const AssistantMessage = () => (
  <MessagePrimitive.Root>
    <MessagePrimitive.Content />
  </MessagePrimitive.Root>
)

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ className }) => {
  const dispatch = useDispatch()
  const currentSessionId = useSelector(selectCurrentSessionId)
  
  // Initialize session ID if not exists
  useEffect(() => {
    if (!currentSessionId) {
      const newSessionId = generateSessionId() // Will use actual user ID when auth is integrated
      dispatch(setCurrentSessionId(newSessionId))
    }
  }, [currentSessionId, dispatch])

  const runtime = useChatRuntime({
    transport: new DefaultChatTransport({
      api: '/conversation/send',
    })
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatContainer className={className}>
        <ChatHeader>
          <MessageCircle size={20} />
          <ChatTitle>AI Financial Assistant</ChatTitle>
        </ChatHeader>
        
        <StyledThreadContainer>
          <ThreadPrimitive.Root className="thread-root">
            <ThreadPrimitive.Viewport className="thread-viewport">
              <ThreadPrimitive.Empty>
                <div style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  padding: '2rem',
                  textAlign: 'center'
                }}>
                  <MessageCircle size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', fontWeight: 500 }}>
                    Start a conversation
                  </h4>
                  <p style={{ margin: 0, fontSize: '1rem', opacity: 0.7 }}>
                    Ask me about your finances, spending patterns, or any questions about managing your money.
                  </p>
                </div>
              </ThreadPrimitive.Empty>
              
              <ThreadPrimitive.Messages
                components={{
                  UserMessage,
                  AssistantMessage,
                  EditComposer: () => null,
                }}
              />
            </ThreadPrimitive.Viewport>
            
            <ComposerPrimitive.Root className="composer-root">
              <ComposerPrimitive.Input 
                className="composer-input"
                placeholder="Ask me about your finances..."
                autoFocus
              />
              <ComposerPrimitive.Send className="composer-send">
                <Send size={16} />
              </ComposerPrimitive.Send>
            </ComposerPrimitive.Root>
          </ThreadPrimitive.Root>
        </StyledThreadContainer>
      </ChatContainer>
    </AssistantRuntimeProvider>
  )
}