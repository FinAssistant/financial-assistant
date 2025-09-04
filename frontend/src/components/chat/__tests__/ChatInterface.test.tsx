import React from "react";
import { screen } from "@testing-library/react";
import { ThemeProvider } from "styled-components";
import { ChatInterface } from "../ChatInterface";
import { theme } from "../../../styles/theme";
import * as aiSDKAdapter from "@assistant-ui/react-ai-sdk";
import * as ai from "ai";
import { renderWithProviders } from "../../../tests/setupTests";

// Mock the Assistant UI components
jest.mock("@assistant-ui/react", () => ({
  AssistantRuntimeProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="runtime-provider">{children}</div>
  ),
  ThreadPrimitive: {
    Root: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="thread-root">{children}</div>
    ),
    Viewport: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="thread-viewport">{children}</div>
    ),
    Empty: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="thread-empty">{children}</div>
    ),
    Messages: () => <div data-testid="thread-messages">Messages</div>,
    If: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="thread-if">{children}</div>
    ),
  },
  ComposerPrimitive: {
    Root: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="composer-root">{children}</div>
    ),
    Input: ({ placeholder, ...props }: { [key: string]: string }) => (
      <input
        data-testid="composer-input"
        placeholder={placeholder}
        {...props}
      />
    ),
    Send: ({ children }: { children: React.ReactNode }) => (
      <button data-testid="composer-send">{children}</button>
    ),
  },
  MessagePrimitive: {
    Root: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="message-root">{children}</div>
    ),
    Content: () => <div data-testid="message-content">Message content</div>,
  },
}));

// Mock the AI SDK adapter
jest.mock("@assistant-ui/react-ai-sdk", () => ({
  useChatRuntime: jest.fn(() => ({
    messages: [],
    isRunning: false,
  })),
}));

// Mock the AI transport
jest.mock("ai", () => ({
  DefaultChatTransport: jest.fn().mockImplementation(() => ({})),
}));

const renderWithTheme = (component: React.ReactElement) => {
  return renderWithProviders(
    <ThemeProvider theme={theme}>{component}</ThemeProvider>,
    {
      conversation: { currentSessionId: "session_1", isLoading: false },
      auth: { isAuthenticated: true, token: "fake-token" },
    }
  );
};

describe("ChatInterface", () => {
  it("renders the chat interface with header", () => {
    renderWithTheme(<ChatInterface />);

    expect(screen.getByText("AI Financial Assistant")).toBeInTheDocument();
    expect(screen.getByTestId("runtime-provider")).toBeInTheDocument();
    expect(screen.getByTestId("thread-root")).toBeInTheDocument();
  });

  it("applies custom className when provided", () => {
    renderWithTheme(<ChatInterface className="custom-chat" />);

    // The className should be applied to the ChatContainer
    expect(
      screen.getByText("AI Financial Assistant").closest(".custom-chat")
    ).toBeInTheDocument();
  });

  it("renders the message circle icon in header", () => {
    renderWithTheme(<ChatInterface />);

    // The MessageCircle from lucide-react should be present
    const header = screen.getByText("AI Financial Assistant").parentElement;
    expect(header).toBeInTheDocument();
  });

  it("integrates with Assistant UI and styled components", () => {
    renderWithTheme(<ChatInterface />);

    // Check that both Assistant UI and styled components are integrated
    expect(screen.getByTestId("runtime-provider")).toBeInTheDocument();
    expect(screen.getByTestId("thread-root")).toBeInTheDocument();
    expect(screen.getByText("AI Financial Assistant")).toBeInTheDocument();
  });

  it("uses correct API endpoint configuration", () => {
    const mockUseChatRuntime = jest.mocked(aiSDKAdapter.useChatRuntime);
    const mockDefaultChatTransport = jest.mocked(ai.DefaultChatTransport);

    renderWithTheme(<ChatInterface />);

    expect(mockDefaultChatTransport).toHaveBeenCalledWith({
      api: "/conversation/send",
      headers: {
        Authorization: "Bearer fake-token",
        "Content-Type": "application/json",
      },
    });
    expect(mockUseChatRuntime).toHaveBeenCalledWith({
      transport: expect.any(Object),
    });
  });
});
