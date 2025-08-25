import React, { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  useLoginAuthLoginPostMutation,
  useRegisterAuthRegisterPostMutation,
} from '../../store/api/authApi'
import { selectIsAuthenticated, selectIsLoading } from '../../store/slices/authSlice'
import {
  Container,
  FormContainer,
  Title,
  Form,
  InputGroup,
  Label,
  Input,
  Button,
  ErrorMessage,
  LoadingSpinner,
  ToggleText,
  ToggleLink,
  PasswordRequirements,
} from './styles'

const LoginPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
  })
  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isLoading = useSelector(selectIsLoading)

  const [login, { isLoading: isLoginLoading, error: loginError }] = useLoginAuthLoginPostMutation()
  const [register, { isLoading: isRegisterLoading, error: registerError }] = useRegisterAuthRegisterPostMutation()

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
    const errors: string[] = []
    
    if (password.length < 8) errors.push('At least 8 characters')
    if (!/[a-z]/.test(password)) errors.push('One lowercase letter')
    if (!/[A-Z]/.test(password)) errors.push('One uppercase letter')
    if (!/\d/.test(password)) errors.push('One number')
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) errors.push('One special character')
    
    return { isValid: errors.length === 0, errors }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Reset errors
    setErrors({})
    
    // Validation
    const newErrors: { [key: string]: string } = {}
    
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Invalid email format'
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required'
    }
    
    if (!isLogin) {
      if (!formData.name.trim()) {
        newErrors.name = 'Name is required'
      }
      
      const passwordValidation = validatePassword(formData.password)
      if (!passwordValidation.isValid) {
        newErrors.password = `Password must have: ${passwordValidation.errors.join(', ')}`
      }
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }
    
    try {
      if (isLogin) {
        await login({
          loginRequest: {
            email: formData.email,
            password: formData.password,
          },
        }).unwrap()
      } else {
        await register({
          registerRequest: {
            email: formData.email,
            password: formData.password,
            name: formData.name || undefined,
          },
        }).unwrap()
      }
    } catch (error) {
      console.error('Authentication error:', error)
      // Error handling is done by RTK Query and the authSlice
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    setFormData({ email: '', password: '', name: '' })
    setErrors({})
  }

  const currentError = loginError || registerError
  const currentLoading = isLoginLoading || isRegisterLoading || isLoading

  return (
    <Container>
      <FormContainer>
        <Title>{isLogin ? 'Sign In' : 'Create Account'}</Title>
        
        <Form onSubmit={handleSubmit}>
          {!isLogin && (
            <InputGroup>
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Enter your full name"
                $hasError={!!errors.name}
              />
              {errors.name && <ErrorMessage>{errors.name}</ErrorMessage>}
            </InputGroup>
          )}
          
          <InputGroup>
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Enter your email"
              $hasError={!!errors.email}
            />
            {errors.email && <ErrorMessage>{errors.email}</ErrorMessage>}
          </InputGroup>
          
          <InputGroup>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              $hasError={!!errors.password}
            />
            {errors.password && <ErrorMessage>{errors.password}</ErrorMessage>}
            
            {!isLogin && (
              <PasswordRequirements>
                <p>Password must contain:</p>
                <ul>
                  <li>At least 8 characters</li>
                  <li>One lowercase letter</li>
                  <li>One uppercase letter</li>
                  <li>One number</li>
                  <li>One special character (!@#$%^&*etc.)</li>
                </ul>
              </PasswordRequirements>
            )}
          </InputGroup>
          
          {currentError && (
            <ErrorMessage>
              {'data' in currentError && currentError.data && typeof currentError.data === 'object' && 'detail' in currentError.data
                ? (currentError.data as { detail: string }).detail 
                : 'An error occurred. Please try again.'}
            </ErrorMessage>
          )}
          
          <Button type="submit" disabled={currentLoading}>
            {currentLoading ? (
              <LoadingSpinner />
            ) : (
              isLogin ? 'Sign In' : 'Create Account'
            )}
          </Button>
        </Form>
        
        <ToggleText>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <ToggleLink onClick={toggleMode}>
            {isLogin ? 'Sign up' : 'Sign in'}
          </ToggleLink>
        </ToggleText>
      </FormContainer>
    </Container>
  )
}

export default LoginPage