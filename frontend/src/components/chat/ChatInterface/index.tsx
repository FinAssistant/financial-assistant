import React, { useEffect, useState } from "react";
import { MessageCircle, Send } from "lucide-react";
import { useSelector, useDispatch } from "react-redux";
import {
  AssistantRuntimeProvider,
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import {
  selectCurrentSessionId,
  setCurrentSessionId,
} from "../../../store/slices/conversationSlice";
import {
  selectToken,
  selectIsAuthenticated,
} from "../../../store/slices/authSlice";
import {
  ChatContainer,
  ChatHeader,
  ChatTitle,
  StyledThreadContainer,
  LoadingIndicator,
  LoadingText,
  SpinningIcon,
  UserMessageContainer,
  AssistantMessageContainer,
  MessageBubble,
} from "./styles";
import { DefaultChatTransport } from "ai";
import { logout } from "../../../store/slices/authSlice";
import { PlaidConnect } from "../../onboarding/PlaidConnect";
import { parseMessageForPlaidData, extractGuidanceText } from "../../../utils/messageUtils";
import { useExchangePublicTokenPlaidExchangePostMutation } from "../../../store/api/generated";
import { PlaidLinkOnEvent, PlaidLinkOnExit, PlaidLinkOnSuccess } from "react-plaid-link";

interface ChatInterfaceProps {
  className?: string;
}

// Generate session ID consistent with backend pattern: f"session_{user_id}"
const generateSessionId = (userId?: string): string => {
  return userId ? `session_${userId}` : `session_guest_${Date.now()}`;
};

// Styled message components
const UserMessage = () => (
  <UserMessageContainer>
    <MessagePrimitive.Root>
      <MessageBubble isUser>
        <MessagePrimitive.Content />
      </MessageBubble>
    </MessagePrimitive.Root>
  </UserMessageContainer>
);

// Enhanced AssistantMessage that can handle Plaid integration
const AssistantMessage = ({
  onPlaidSuccess,
  onPlaidEvent,
  onPlaidExit
}: {
  onPlaidSuccess?: PlaidLinkOnSuccess;
  onPlaidEvent?: PlaidLinkOnEvent;
  onPlaidExit?: PlaidLinkOnExit;
}) => {
  return (
    <AssistantMessageContainer>
      <MessagePrimitive.Root>
        <MessageBubble>
          <MessagePrimitive.Content
            components={{
              Text: ({ text }) => {
                const plaidData = parseMessageForPlaidData(text);

                if (plaidData && onPlaidSuccess && onPlaidEvent && onPlaidExit) {
                  const guidanceText = extractGuidanceText(text);
                  return (
                    <>
                      {guidanceText && <p>{guidanceText}</p>}
                      <PlaidConnect
                        linkToken={plaidData.link_token}
                        onSuccess={onPlaidSuccess}
                        onEvent={onPlaidEvent}
                        onExit={onPlaidExit}
                      />
                    </>
                  );
                }

                return <p>{text}</p>;
              }
            }}
          />
        </MessageBubble>
      </MessagePrimitive.Root>
    </AssistantMessageContainer>
  );
};

// Loading indicator component for when assistant is thinking
const AssistantThinking = () => (
  <LoadingIndicator>
    <SpinningIcon size={16} />
    <LoadingText>AI is thinking...</LoadingText>
  </LoadingIndicator>
);

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ className }) => {
  const dispatch = useDispatch();
  const currentSessionId = useSelector(selectCurrentSessionId);
  const token = useSelector(selectToken);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const [exchangeToken, { isLoading: isExchanging }] = useExchangePublicTokenPlaidExchangePostMutation();
  const [plaidError, setPlaidError] = useState<string | null>(null);

  // Initialize session ID if not exists
  useEffect(() => {
    if (!currentSessionId) {
      const newSessionId = generateSessionId(); // Will use actual user ID when auth is integrated
      dispatch(setCurrentSessionId(newSessionId));
    }
  }, [currentSessionId, dispatch]);

  // Custom fetch function that handles 401 errors like RTK Query
  const customFetch: typeof fetch = async (url, options) => {
    const response = await fetch(url, options);

    // If we get a 401 error, handle it like RTK Query
    if (response.status === 401) {
      console.log('Token expired, logging out and redirecting to login page');
      dispatch(logout());
    }

    return response;
  };

  const runtime = useChatRuntime({
    transport: new DefaultChatTransport({
      api: "/conversation/send",
      headers:
        isAuthenticated && token
          ? {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            }
          : undefined,
      fetch: customFetch,
    }),
  });

  // Plaid event handlers
  const handlePlaidSuccess = async (publicToken: string) => {
    try {
      setPlaidError(null);
      const result = await exchangeToken({
        plaidTokenExchangeRequest: {
          public_token: publicToken,
          session_id: currentSessionId
        }
      }).unwrap();

      console.log('Plaid connection successful:', result);

      // Backend automatically injects system message and continues conversation
      // No manual message sending needed - the backend handles conversation flow

    } catch (error) {
      console.error('Plaid connection error:', error);
      setPlaidError(JSON.stringify(error));
    }
  };

  const handlePlaidEvent: PlaidLinkOnEvent = (eventName, metadata) => {
    console.error('Plaid Link event:', eventName, metadata);
  };

  const handlePlaidExit: PlaidLinkOnExit = (error, metadata) => {
    if (error) {
      console.error('Plaid Link error on exit:', error, metadata);
      setPlaidError(error.display_message || error.error_message || 'An error occurred during Plaid connection');
    } else {
      // For user cancellation, we can show a local message or let them continue manually
      // The backend conversation flow remains uninterrupted
      console.log('User cancelled Plaid connection');
      setPlaidError(null);
    }
  };

  // Show simple message if not authenticated (should not happen due to routing)
  if (!isAuthenticated || !token) {
    return (
      <ChatContainer className={className}>
        <ChatHeader>
          <MessageCircle size={20} />
          <ChatTitle>AI Financial Assistant</ChatTitle>
        </ChatHeader>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flex: 1,
            padding: "2rem",
          }}
        >
          <p>Authentication required</p>
        </div>
      </ChatContainer>
    );
  }

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
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "2rem",
                    textAlign: "center",
                  }}
                >
                  <MessageCircle
                    size={48}
                    style={{ marginBottom: "1rem", opacity: 0.5 }}
                  />
                  <h4
                    style={{
                      margin: "0 0 0.5rem 0",
                      fontSize: "1.125rem",
                      fontWeight: 500,
                    }}
                  >
                    Start a conversation
                  </h4>
                  <p style={{ margin: 0, fontSize: "1rem", opacity: 0.7 }}>
                    Ask me about your finances, spending patterns, or any
                    questions about managing your money.
                  </p>
                </div>
              </ThreadPrimitive.Empty>

              <ThreadPrimitive.Messages
                components={{
                  UserMessage,
                  AssistantMessage: () => (
                    <AssistantMessage
                      onPlaidSuccess={handlePlaidSuccess}
                      onPlaidEvent={handlePlaidEvent}
                      onPlaidExit={handlePlaidExit}
                    />
                  ),
                  EditComposer: () => null,
                }}
              />

              <ThreadPrimitive.If running>
                <AssistantThinking />
              </ThreadPrimitive.If>

              {/* Plaid error display */}
              {plaidError && (
                <div style={{
                  margin: '16px',
                  padding: '12px 16px',
                  backgroundColor: '#fee2e2',
                  color: '#dc2626',
                  borderRadius: '6px',
                  border: '1px solid #fecaca',
                  fontSize: '14px'
                }}>
                  <strong>Connection Error:</strong> {plaidError}
                </div>
              )}

              {/* Plaid loading indicator */}
              {isExchanging && (
                <div style={{
                  margin: '16px',
                  padding: '12px 16px',
                  backgroundColor: '#f0f9ff',
                  color: '#0369a1',
                  borderRadius: '6px',
                  border: '1px solid #bae6fd',
                  fontSize: '14px'
                }}>
                  <strong>Processing:</strong> Connecting your account...
                </div>
              )}
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
  );
};
