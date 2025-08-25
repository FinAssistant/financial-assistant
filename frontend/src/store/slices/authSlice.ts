import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { authApi } from '../api/authApi'

export interface User {
  id: string
  email: string
  name?: string
  profile_complete: boolean
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  loading: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      state.loading = false
    },
    setCredentials: (state, action: PayloadAction<{ user: User; token: string }>) => {
      const { user, token } = action.payload
      state.user = user
      state.token = token
      state.isAuthenticated = true
      state.loading = false
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
  },
  extraReducers: (builder) => {
    // Handle register
    builder
      .addMatcher(authApi.endpoints.registerAuthRegisterPost.matchPending, (state) => {
        state.loading = true
      })
      .addMatcher(authApi.endpoints.registerAuthRegisterPost.matchFulfilled, (state, action) => {
        const { access_token, user } = action.payload
        state.user = user as User
        state.token = access_token
        state.isAuthenticated = true
        state.loading = false
      })
      .addMatcher(authApi.endpoints.registerAuthRegisterPost.matchRejected, (state) => {
        state.loading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
      })

    // Handle login
    builder
      .addMatcher(authApi.endpoints.loginAuthLoginPost.matchPending, (state) => {
        state.loading = true
      })
      .addMatcher(authApi.endpoints.loginAuthLoginPost.matchFulfilled, (state, action) => {
        const { access_token, user } = action.payload
        state.user = user as User
        state.token = access_token
        state.isAuthenticated = true
        state.loading = false
      })
      .addMatcher(authApi.endpoints.loginAuthLoginPost.matchRejected, (state) => {
        state.loading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
      })

    // Handle logout
    builder
      .addMatcher(authApi.endpoints.logoutAuthLogoutPost.matchFulfilled, (state) => {
        state.user = null
        state.token = null
        state.isAuthenticated = false
        state.loading = false
      })
  },
})

export const { logout, setCredentials, setLoading } = authSlice.actions

export default authSlice.reducer

// Selectors
export const selectCurrentUser = (state: { auth: AuthState }) => state.auth.user
export const selectToken = (state: { auth: AuthState }) => state.auth.token
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectIsLoading = (state: { auth: AuthState }) => state.auth.loading