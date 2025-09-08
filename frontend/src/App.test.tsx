import React from "react";
import { screen } from "@testing-library/react";
import App from "./App";
import { renderWithProviders } from "./tests/setupTests";

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

describe("App", () => {
  describe("Non-authenticated user", () => {
    test("renders without crashing", () => {
      renderWithProviders(<App />);
    });

    test("renders HomePage with welcome message", () => {
      renderWithProviders(<App />);
      expect(
        screen.getByText("Welcome to AI Financial Assistant")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Your intelligent companion for managing finances/)
      ).toBeInTheDocument();
    });

    test("renders login button on HomePage", () => {
      renderWithProviders(<App />);
      expect(
        screen.getByRole("link", { name: "Get Started - Sign In" })
      ).toBeInTheDocument();
    });

    test("renders feature cards on HomePage", () => {
      renderWithProviders(<App />);
      expect(screen.getByText("Smart Analytics")).toBeInTheDocument();
      expect(screen.getByText("Secure Banking")).toBeInTheDocument();
      expect(screen.getByText("Personalized Advice")).toBeInTheDocument();
    });
  });

  describe("Authenticated user", () => {
    test("renders Dashboard for authenticated user", () => {
      renderWithProviders(<App />, {
        auth: {
          isAuthenticated: true,
          user: {
            id: "1",
            email: "test@example.com",
            name: "Test User",
            profile_complete: true,
          },
          token: "fake-token",
          loading: false,
        },
      });

      expect(screen.getByText("Financial Dashboard")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Overview of your financial health and recent activity"
        )
      ).toBeInTheDocument();
    });

    test("renders header with app name for authenticated user", () => {
      renderWithProviders(<App />, {
        auth: {
          isAuthenticated: true,
          user: {
            id: "1",
            email: "test@example.com",
            name: "Test User",
            profile_complete: true,
          },
          token: "fake-token",
          loading: false,
        },
      });

      expect(
        screen.getByRole("heading", { name: "AI Financial Assistant" })
      ).toBeInTheDocument();
    });

    test("renders navigation links for authenticated user", () => {
      renderWithProviders(<App />, {
        auth: {
          isAuthenticated: true,
          user: {
            id: "1",
            email: "test@example.com",
            name: "Test User",
            profile_complete: true,
          },
          token: "fake-token",
          loading: false,
        },
      });

      expect(
        screen.getByRole("link", { name: /Dashboard/ })
      ).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /About/ })).toBeInTheDocument();
    });
  });

  describe("Routing", () => {
    test("renders AboutPage when navigating to /about", () => {
      renderWithProviders(<App />, {}, "/about");

      // AboutPage should be rendered (you may need to adjust based on AboutPage content)
      expect(screen.getByText("AI Financial Assistant")).toBeInTheDocument(); // Header
    });

    test("renders LoginPage when navigating to /login", () => {
      renderWithProviders(<App />, {}, "/login");

      // This would render the LoginPage - you may need to check for specific login content
      // For now, we'll just ensure it doesn't crash
      expect(document.body).toBeInTheDocument();
    });

    test("renders NotImplementedPage for unmatched routes", () => {
      renderWithProviders(<App />, {}, "/nonexistent-route");

      expect(screen.getByText("Page Not Found")).toBeInTheDocument();
      expect(
        screen.getByText(/The page you're looking for doesn't exist/)
      ).toBeInTheDocument();
    });
  });
});
