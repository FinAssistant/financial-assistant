import { createApi, fetchBaseQuery, BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query/react'
import type { RootState } from '../index'

const baseQuery = fetchBaseQuery({
  baseUrl: '',
  prepareHeaders: (headers, { getState }) => {
    // Get token from auth state
    const token = (getState() as RootState).auth.token

    // If we have a token set in state, use it for authenticated requests
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }

    return headers
  },
})

const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const result = await baseQuery(args, api, extraOptions)

  // If we get a 401 error, the token might be expired
  if (result.error && result.error.status === 401) {
    // Get current auth state
    const state = api.getState() as RootState

    // If user was authenticated, log them out
    if (state.auth.isAuthenticated) {
      // Import logout dynamically to avoid circular dependency
      const { logout } = await import('../slices/authSlice')
      api.dispatch(logout())

      // Force redirect to login page immediately
      console.log('Token expired, logging out and redirecting to login page')
      window.location.href = '/login'
    } else {
      console.log('User not authenticated, allowing error to bubble up for login form')
    }
  }

  return result
}

export const baseApi = createApi({
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Auth', 'User'],
  endpoints: () => ({}),
})