import { baseApi as api } from "./baseApi";
export const addTagTypes = ["authentication", "conversation", "plaid"] as const;
const injectedRtkApi = api
  .enhanceEndpoints({
    addTagTypes,
  })
  .injectEndpoints({
    endpoints: (build) => ({
      registerAuthRegisterPost: build.mutation<
        RegisterAuthRegisterPostApiResponse,
        RegisterAuthRegisterPostApiArg
      >({
        query: (queryArg) => ({
          url: `/auth/register`,
          method: "POST",
          body: queryArg.registerRequest,
        }),
        invalidatesTags: ["authentication"],
      }),
      loginAuthLoginPost: build.mutation<
        LoginAuthLoginPostApiResponse,
        LoginAuthLoginPostApiArg
      >({
        query: (queryArg) => ({
          url: `/auth/login`,
          method: "POST",
          body: queryArg.loginRequest,
        }),
        invalidatesTags: ["authentication"],
      }),
      logoutAuthLogoutPost: build.mutation<
        LogoutAuthLogoutPostApiResponse,
        LogoutAuthLogoutPostApiArg
      >({
        query: () => ({ url: `/auth/logout`, method: "POST" }),
        invalidatesTags: ["authentication"],
      }),
      getCurrentUserInfoAuthMeGet: build.query<
        GetCurrentUserInfoAuthMeGetApiResponse,
        GetCurrentUserInfoAuthMeGetApiArg
      >({
        query: () => ({ url: `/auth/me` }),
        providesTags: ["authentication"],
      }),
      sendMessageConversationSendPost: build.mutation<
        SendMessageConversationSendPostApiResponse,
        SendMessageConversationSendPostApiArg
      >({
        query: (queryArg) => ({
          url: `/conversation/send`,
          method: "POST",
          body: queryArg.conversationRequest,
        }),
        invalidatesTags: ["conversation"],
      }),
      sendMessageNonStreamingConversationMessagePost: build.mutation<
        SendMessageNonStreamingConversationMessagePostApiResponse,
        SendMessageNonStreamingConversationMessagePostApiArg
      >({
        query: (queryArg) => ({
          url: `/conversation/message`,
          method: "POST",
          body: queryArg.conversationRequest,
        }),
        invalidatesTags: ["conversation"],
      }),
      healthCheckConversationHealthGet: build.query<
        HealthCheckConversationHealthGetApiResponse,
        HealthCheckConversationHealthGetApiArg
      >({
        query: () => ({ url: `/conversation/health` }),
        providesTags: ["conversation"],
      }),
      exchangePublicTokenApiPlaidExchangePost: build.mutation<
        ExchangePublicTokenApiPlaidExchangePostApiResponse,
        ExchangePublicTokenApiPlaidExchangePostApiArg
      >({
        query: (queryArg) => ({
          url: `/api/plaid/exchange`,
          method: "POST",
          body: queryArg.plaidTokenExchangeRequest,
        }),
        invalidatesTags: ["plaid"],
      }),
      getConnectedAccountsApiPlaidAccountsGet: build.query<
        GetConnectedAccountsApiPlaidAccountsGetApiResponse,
        GetConnectedAccountsApiPlaidAccountsGetApiArg
      >({
        query: () => ({ url: `/api/plaid/accounts` }),
        providesTags: ["plaid"],
      }),
      disconnectAccountApiPlaidAccountsAccountIdDelete: build.mutation<
        DisconnectAccountApiPlaidAccountsAccountIdDeleteApiResponse,
        DisconnectAccountApiPlaidAccountsAccountIdDeleteApiArg
      >({
        query: (queryArg) => ({
          url: `/api/plaid/accounts/${queryArg.accountId}`,
          method: "DELETE",
        }),
        invalidatesTags: ["plaid"],
      }),
      healthCheckHealthGet: build.query<
        HealthCheckHealthGetApiResponse,
        HealthCheckHealthGetApiArg
      >({
        query: () => ({ url: `/health` }),
      }),
      apiHealthCheckApiHealthGet: build.query<
        ApiHealthCheckApiHealthGetApiResponse,
        ApiHealthCheckApiHealthGetApiArg
      >({
        query: () => ({ url: `/api/health` }),
      }),
      serveReactAppFullPathGet: build.query<
        ServeReactAppFullPathGetApiResponse,
        ServeReactAppFullPathGetApiArg
      >({
        query: (queryArg) => ({ url: `/${queryArg.fullPath}` }),
      }),
    }),
    overrideExisting: false,
  });
export { injectedRtkApi as api };
export type RegisterAuthRegisterPostApiResponse =
  /** status 201 Successful Response */ AuthResponse;
export type RegisterAuthRegisterPostApiArg = {
  registerRequest: RegisterRequest;
};
export type LoginAuthLoginPostApiResponse =
  /** status 200 Successful Response */ AuthResponse;
export type LoginAuthLoginPostApiArg = {
  loginRequest: LoginRequest;
};
export type LogoutAuthLogoutPostApiResponse =
  /** status 200 Successful Response */ MessageResponse;
export type LogoutAuthLogoutPostApiArg = void;
export type GetCurrentUserInfoAuthMeGetApiResponse =
  /** status 200 Successful Response */ {
    [key: string]: any;
  };
export type GetCurrentUserInfoAuthMeGetApiArg = void;
export type SendMessageConversationSendPostApiResponse =
  /** status 200 Successful Response */ void;
export type SendMessageConversationSendPostApiArg = {
  conversationRequest: ConversationRequest;
};
export type SendMessageNonStreamingConversationMessagePostApiResponse =
  /** status 200 Successful Response */ ConversationResponse;
export type SendMessageNonStreamingConversationMessagePostApiArg = {
  conversationRequest: ConversationRequest;
};
export type HealthCheckConversationHealthGetApiResponse =
  /** status 200 Successful Response */ ConversationHealthResponse;
export type HealthCheckConversationHealthGetApiArg = void;
export type ExchangePublicTokenApiPlaidExchangePostApiResponse =
  /** status 200 Successful Response */ PlaidTokenExchangeResponse;
export type ExchangePublicTokenApiPlaidExchangePostApiArg = {
  plaidTokenExchangeRequest: PlaidTokenExchangeRequest;
};
export type GetConnectedAccountsApiPlaidAccountsGetApiResponse =
  /** status 200 Successful Response */ {
    [key: string]: any;
  }[];
export type GetConnectedAccountsApiPlaidAccountsGetApiArg = void;
export type DisconnectAccountApiPlaidAccountsAccountIdDeleteApiResponse =
  /** status 200 Successful Response */ {
    [key: string]: any;
  };
export type DisconnectAccountApiPlaidAccountsAccountIdDeleteApiArg = {
  accountId: string;
};
export type HealthCheckHealthGetApiResponse =
  /** status 200 Successful Response */ any;
export type HealthCheckHealthGetApiArg = void;
export type ApiHealthCheckApiHealthGetApiResponse =
  /** status 200 Successful Response */ any;
export type ApiHealthCheckApiHealthGetApiArg = void;
export type ServeReactAppFullPathGetApiResponse =
  /** status 200 Successful Response */ any;
export type ServeReactAppFullPathGetApiArg = {
  fullPath: string;
};
export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user: {
    [key: string]: any;
  };
};
export type ValidationError = {
  loc: (string | number)[];
  msg: string;
  type: string;
};
export type HttpValidationError = {
  detail?: ValidationError[];
};
export type RegisterRequest = {
  email: string;
  password: string;
  name?: string | null;
};
export type LoginRequest = {
  email: string;
  password: string;
};
export type MessageResponse = {
  message: string;
};
export type MessagePart = {
  /** Part type: text, image, etc. */
  type: string;
  /** Text content for text parts */
  text: string;
};
export type ClientMessage = {
  /** Message ID */
  id: string;
  /** Message role: user, assistant, or system */
  role: string;
  /** Message parts array */
  parts: MessagePart[];
};
export type ConversationRequest = {
  /** Array of conversation messages */
  messages: ClientMessage[];
  /** Optional conversation session ID */
  session_id?: string | null;
};
export type ConversationResponse = {
  id: string;
  content: string;
  role: string;
  agent: string;
  session_id: string;
  user_id: string;
  created_at: string;
};
export type ConversationHealthResponse = {
  status: string;
  graph_initialized: boolean;
  llm_available: boolean;
  test_response_received: boolean;
  error?: string | null;
};
export type PlaidTokenExchangeResponse = {
  /** Operation status */
  status: string;
  /** Human-readable message */
  message: string;
  /** Number of accounts connected */
  accounts_connected: number;
  /** List of connected account IDs */
  account_ids?: string[];
};
export type PlaidTokenExchangeRequest = {
  /** Public token from Plaid Link */
  public_token: string;
  /** Optional session ID for conversation resumption */
  session_id?: string | null;
};
export const {
  useRegisterAuthRegisterPostMutation,
  useLoginAuthLoginPostMutation,
  useLogoutAuthLogoutPostMutation,
  useGetCurrentUserInfoAuthMeGetQuery,
  useSendMessageConversationSendPostMutation,
  useSendMessageNonStreamingConversationMessagePostMutation,
  useHealthCheckConversationHealthGetQuery,
  useExchangePublicTokenApiPlaidExchangePostMutation,
  useGetConnectedAccountsApiPlaidAccountsGetQuery,
  useDisconnectAccountApiPlaidAccountsAccountIdDeleteMutation,
  useHealthCheckHealthGetQuery,
  useApiHealthCheckApiHealthGetQuery,
  useServeReactAppFullPathGetQuery,
} = injectedRtkApi;
