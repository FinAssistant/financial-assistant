import React from 'react'
import { MessageCircle } from 'lucide-react'
import { 
  AssistantRuntimeProvider, 
} from '@assistant-ui/react'
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import {
  ChatContainer,
  ChatHeader,
  ChatTitle,
  StyledThread,
} from './styles'
import { DefaultChatTransport } from 'ai';

interface ChatInterfaceProps {
  className?: string
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ className }) => {
  
const runtime = useChatRuntime({
  transport: new DefaultChatTransport({
    api: '/api/conversation/send',
  })
});

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatContainer className={className}>
        <ChatHeader>
          <MessageCircle size={20} />
          <ChatTitle>AI Financial Assistant</ChatTitle>
        </ChatHeader>
        
        <StyledThread />
      </ChatContainer>
    </AssistantRuntimeProvider>
  )
}