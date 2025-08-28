import { baseApi as api } from "./baseApi";
export const addTagTypes = ["authentication", "conversation"] as const;
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
    }),
    overrideExisting: false,
  });
export { injectedRtkApi as apiSlice };
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
export type HealthCheckHealthGetApiResponse =
  /** status 200 Successful Response */ any;
export type HealthCheckHealthGetApiArg = void;
export type ApiHealthCheckApiHealthGetApiResponse =
  /** status 200 Successful Response */ any;
export type ApiHealthCheckApiHealthGetApiArg = void;
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
export type ConversationRequest = {
  /** User message */
  message: string;
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
  test_response_received: boolean;
  error?: string | null;
};
export const {
  useRegisterAuthRegisterPostMutation,
  useLoginAuthLoginPostMutation,
  useLogoutAuthLogoutPostMutation,
  useGetCurrentUserInfoAuthMeGetQuery,
  useSendMessageConversationSendPostMutation,
  useSendMessageNonStreamingConversationMessagePostMutation,
  useHealthCheckConversationHealthGetQuery,
  useHealthCheckHealthGetQuery,
  useApiHealthCheckApiHealthGetQuery,
} = injectedRtkApi;
