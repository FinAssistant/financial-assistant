import { baseApi as api } from "./baseApi";
export const addTagTypes = ["authentication"] as const;
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
export { injectedRtkApi as authApi };
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
    id: string;
    email: string;
    name?: string;
    profile_complete: boolean;
    created_at?: string;
  };
export type GetCurrentUserInfoAuthMeGetApiArg = void;
export type HealthCheckHealthGetApiResponse =
  /** status 200 Successful Response */ Record<string, unknown>;
export type HealthCheckHealthGetApiArg = void;
export type ApiHealthCheckApiHealthGetApiResponse =
  /** status 200 Successful Response */ Record<string, unknown>;
export type ApiHealthCheckApiHealthGetApiArg = void;
export type ServeReactAppFullPathGetApiResponse =
  /** status 200 Successful Response */ Record<string, unknown>;
export type ServeReactAppFullPathGetApiArg = {
  fullPath: string;
};
export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user: {
    id: string;
    email: string;
    name?: string;
    profile_complete: boolean;
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
export const {
  useRegisterAuthRegisterPostMutation,
  useLoginAuthLoginPostMutation,
  useLogoutAuthLogoutPostMutation,
  useGetCurrentUserInfoAuthMeGetQuery,
  useHealthCheckHealthGetQuery,
  useApiHealthCheckApiHealthGetQuery,
  useServeReactAppFullPathGetQuery,
} = injectedRtkApi;
