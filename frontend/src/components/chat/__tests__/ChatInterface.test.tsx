import React from 'react'
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import { ChatInterface } from '../ChatInterface'
import { theme } from '../../../styles/theme'
import * as aiSDKAdapter from '@assistant-ui/react-ai-sdk'
import * as ai from 'ai'

// Mock the Assistant UI components
jest.mock('@assistant-ui/react', () => ({
  AssistantRuntimeProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="runtime-provider">{children}</div>,
  ThreadPrimitive: {
    Root: ({ children }: { children: React.ReactNode }) => <div data-testid="thread-root">{children}</div>,
  },
}))

// Mock the AI SDK adapter
jest.mock('@assistant-ui/react-ai-sdk', () => ({
  useChatRuntime: jest.fn(() => ({
    messages: [],
    isRunning: false,
  })),
}))

// Mock the AI transport
jest.mock('ai', () => ({
  DefaultChatTransport: jest.fn().mockImplementation(() => ({})),
}))

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  )
}

describe('ChatInterface', () => {
  it('renders the chat interface with header', () => {
    renderWithTheme(<ChatInterface />)
    
    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
    expect(screen.getByTestId('runtime-provider')).toBeInTheDocument()
    expect(screen.getByTestId('thread-root')).toBeInTheDocument()
  })

  it('applies custom className when provided', () => {
    renderWithTheme(<ChatInterface className="custom-chat" />)
    
    // The className should be applied to the ChatContainer
    expect(screen.getByText('AI Financial Assistant').closest('.custom-chat')).toBeInTheDocument()
  })

  it('renders the message circle icon in header', () => {
    renderWithTheme(<ChatInterface />)
    
    // The MessageCircle from lucide-react should be present
    const header = screen.getByText('AI Financial Assistant').parentElement
    expect(header).toBeInTheDocument()
  })

  it('integrates with Assistant UI and styled components', () => {
    renderWithTheme(<ChatInterface />)
    
    // Check that both Assistant UI and styled components are integrated
    expect(screen.getByTestId('runtime-provider')).toBeInTheDocument()
    expect(screen.getByTestId('thread-root')).toBeInTheDocument()
    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
  })

  it('uses correct API endpoint configuration', () => {
    const mockUseChatRuntime = jest.mocked(aiSDKAdapter.useChatRuntime)
    const mockDefaultChatTransport = jest.mocked(ai.DefaultChatTransport)
    
    renderWithTheme(<ChatInterface />)
    
    expect(mockDefaultChatTransport).toHaveBeenCalledWith({
      api: '/api/conversation/send',
    })
    expect(mockUseChatRuntime).toHaveBeenCalledWith({
      transport: expect.any(Object)
    })
  })
})