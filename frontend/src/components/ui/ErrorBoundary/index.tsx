import React, { Component, ErrorInfo, ReactNode } from 'react'
import styled from 'styled-components'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from '../Button'
import { Card } from '../Card'
import { Heading, Text } from '../Typography'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: ${({ theme }) => theme.spacing[8]};
  text-align: center;
`

const ErrorIcon = styled.div`
  color: ${({ theme }) => theme.colors.error.main};
  margin-bottom: ${({ theme }) => theme.spacing[4]};
`

const ErrorTitle = styled(Heading)`
  margin-bottom: ${({ theme }) => theme.spacing[2]};
  color: ${({ theme }) => theme.colors.error.main};
`

const ErrorMessage = styled(Text)`
  margin-bottom: ${({ theme }) => theme.spacing[6]};
  max-width: 500px;
`

const ErrorActions = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing[3]};
  flex-wrap: wrap;
  justify-content: center;
`

const ErrorDetails = styled.details`
  margin-top: ${({ theme }) => theme.spacing[4]};
  text-align: left;
  max-width: 100%;
  width: 600px;
  
  summary {
    cursor: pointer;
    color: ${({ theme }) => theme.colors.text.secondary};
    font-size: ${({ theme }) => theme.fontSizes.sm};
    margin-bottom: ${({ theme }) => theme.spacing[2]};
    
    &:hover {
      color: ${({ theme }) => theme.colors.text.primary};
    }
  }
`

const ErrorStackTrace = styled.pre`
  background: ${({ theme }) => theme.colors.background.tertiary};
  padding: ${({ theme }) => theme.spacing[4]};
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-family: ${({ theme }) => theme.fonts.mono};
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: ${({ theme }) => theme.colors.text.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
`

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { 
      hasError: true, 
      error,
      errorInfo: null 
    }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    })

    // Log the error
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <ErrorContainer>
          <Card variant="outlined" size="lg">
            <Card.Body>
              <ErrorIcon>
                <AlertTriangle size={48} />
              </ErrorIcon>
              
              <ErrorTitle level={2}>Something went wrong</ErrorTitle>
              
              <ErrorMessage color="secondary">
                We're sorry, but something unexpected happened. This error has been logged 
                and our team will investigate the issue.
              </ErrorMessage>
              
              <ErrorActions>
                <Button variant="primary" onClick={this.handleRetry} icon={<RefreshCw size={16} />}>
                  Try Again
                </Button>
                <Button variant="outline" onClick={this.handleGoHome} icon={<Home size={16} />}>
                  Go Home
                </Button>
                <Button variant="ghost" onClick={this.handleReload}>
                  Reload Page
                </Button>
              </ErrorActions>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <ErrorDetails>
                  <summary>Error Details (Development Only)</summary>
                  <ErrorStackTrace>
                    <strong>Error:</strong> {this.state.error.message}
                    {this.state.error.stack && (
                      <>
                        <br /><br />
                        <strong>Stack Trace:</strong><br />
                        {this.state.error.stack}
                      </>
                    )}
                    {this.state.errorInfo && this.state.errorInfo.componentStack && (
                      <>
                        <br /><br />
                        <strong>Component Stack:</strong><br />
                        {this.state.errorInfo.componentStack}
                      </>
                    )}
                  </ErrorStackTrace>
                </ErrorDetails>
              )}
            </Card.Body>
          </Card>
        </ErrorContainer>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

// Higher-order component for easy wrapping
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// Async error boundary for handling promise rejections
export class AsyncErrorBoundary extends ErrorBoundary {
  constructor(props: Props) {
    super(props)
    
    // Handle unhandled promise rejections
    if (typeof window !== 'undefined') {
      window.addEventListener('unhandledrejection', this.handleUnhandledRejection)
    }
  }

  componentWillUnmount() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('unhandledrejection', this.handleUnhandledRejection)
    }
  }

  private handleUnhandledRejection = (event: PromiseRejectionEvent) => {
    const error = new Error(event.reason?.message || 'Unhandled promise rejection')
    error.stack = event.reason?.stack
    
    this.setState({
      hasError: true,
      error,
      errorInfo: null
    })
    
    event.preventDefault()
  }
}