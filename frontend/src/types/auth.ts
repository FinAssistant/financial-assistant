export interface User {
  id: string
  email: string
  name?: string
  profile_complete: boolean
  created_at?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  name?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface AuthError {
  status: number
  data: {
    detail: string
  }
}