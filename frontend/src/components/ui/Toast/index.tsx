import React, { createContext, useContext, useCallback, useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import styled, { css, keyframes } from 'styled-components'
import { AlertTriangle, CheckCircle, Info, X, XCircle } from 'lucide-react'

// Types
interface Toast {
  id: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
  duration?: number
  persistent?: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  removeAllToasts: () => void
}

// Animations
const slideInRight = keyframes`
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`

const slideOutRight = keyframes`
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
`

// Styled Components
const ToastContainer = styled.div`
  position: fixed;
  top: ${({ theme }) => theme.spacing[4]};
  right: ${({ theme }) => theme.spacing[4]};
  z-index: ${({ theme }) => theme.zIndex.toast};
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing[2]};
  max-width: 400px;
  
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}) {
    top: ${({ theme }) => theme.spacing[2]};
    right: ${({ theme }) => theme.spacing[2]};
    left: ${({ theme }) => theme.spacing[2]};
    max-width: none;
  }
`

const ToastItem = styled.div.withConfig({
  shouldForwardProp: (prop) => !['type', 'isExiting'].includes(prop as string),
})<{ type: Toast['type']; isExiting: boolean }>`
  display: flex;
  align-items: flex-start;
  gap: ${({ theme }) => theme.spacing[3]};
  padding: ${({ theme }) => theme.spacing[4]} ${({ theme }) => theme.spacing[5]};
  border-radius: ${({ theme }) => theme.radii.md};
  box-shadow: ${({ theme }) => theme.shadows.lg};
  border: 1px solid;
  position: relative;
  animation: ${({ isExiting }) => isExiting ? slideOutRight : slideInRight} 0.3s ease-out;
  max-width: 100%;
  word-wrap: break-word;
  
  ${({ type, theme }) => {
    switch (type) {
      case 'info':
        return css`
          background: ${theme.colors.background.card};
          border-color: ${theme.colors.primary[200]};
          color: ${theme.colors.text.primary};
        `
      case 'success':
        return css`
          background: ${theme.colors.success[50]};
          border-color: ${theme.colors.success[200]};
          color: ${theme.colors.success[800]};
        `
      case 'warning':
        return css`
          background: ${theme.colors.warning[50]};
          border-color: ${theme.colors.warning[200]};
          color: ${theme.colors.warning[800]};
        `
      case 'error':
        return css`
          background: ${theme.colors.error[50]};
          border-color: ${theme.colors.error[200]};
          color: ${theme.colors.error[800]};
        `
      default:
        return css`
          background: ${theme.colors.background.card};
          border-color: ${theme.colors.primary[200]};
          color: ${theme.colors.text.primary};
        `
    }
  }}
`

const ToastIcon = styled.div<{ type: Toast['type'] }>`
  display: flex;
  align-items: center;
  flex-shrink: 0;
  
  ${({ type, theme }) => {
    switch (type) {
      case 'success':
        return css`color: ${theme.colors.success.main};`
      case 'warning':
        return css`color: ${theme.colors.warning.main};`
      case 'error':
        return css`color: ${theme.colors.error.main};`
      default:
        return css`color: ${theme.colors.primary.main};`
    }
  }}
`

const ToastContent = styled.div`
  flex: 1;
  min-width: 0;
`

const ToastMessage = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  line-height: ${({ theme }) => theme.lineHeights.relaxed};
  margin-bottom: ${({ theme }) => theme.spacing[2]};
  
  &:last-child {
    margin-bottom: 0;
  }
`

const ToastAction = styled.button`
  background: none;
  border: none;
  color: inherit;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: ${({ theme }) => theme.fontWeights.medium};
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing[1]} 0;
  text-decoration: underline;
  
  &:hover {
    opacity: 0.8;
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px currentColor;
    border-radius: 2px;
  }
`

const ToastCloseButton = styled.button`
  position: absolute;
  top: ${({ theme }) => theme.spacing[2]};
  right: ${({ theme }) => theme.spacing[2]};
  background: none;
  border: none;
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing[1]};
  border-radius: ${({ theme }) => theme.radii.sm};
  color: inherit;
  opacity: 0.7;
  transition: ${({ theme }) => theme.transitions.fast};
  
  &:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.05);
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px currentColor;
  }
`

const ToastProgressBar = styled.div<{ duration: number }>`
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: currentColor;
  opacity: 0.3;
  animation: progress ${({ duration }) => duration}ms linear;
  
  @keyframes progress {
    from {
      width: 100%;
    }
    to {
      width: 0%;
    }
  }
`

// Helper function to get icon
const getIcon = (type: Toast['type']) => {
  switch (type) {
    case 'info':
      return <Info size={20} />
    case 'success':
      return <CheckCircle size={20} />
    case 'warning':
      return <AlertTriangle size={20} />
    case 'error':
      return <XCircle size={20} />
    default:
      return <Info size={20} />
  }
}

// Context
const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export const useToast = () => {
  const context = useContext(ToastContext)
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Toast Provider
interface ToastProviderProps {
  children: React.ReactNode
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([])
  const [exitingToasts, setExitingToasts] = useState<Set<string>>(new Set())

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: Toast = {
      id,
      duration: 5000,
      ...toast
    }

    setToasts(prev => [...prev, newToast])

    // Auto remove toast after duration (unless persistent)
    if (!newToast.persistent && newToast.duration) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }

    return id
  }, [])

  const removeToast = useCallback((id: string) => {
    setExitingToasts(prev => new Set(prev).add(id))
    
    // Remove from DOM after animation
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id))
      setExitingToasts(prev => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }, 300)
  }, [])

  const removeAllToasts = useCallback(() => {
    setToasts([])
    setExitingToasts(new Set())
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, removeAllToasts }}>
      {children}
      <ToastRenderer toasts={toasts} exitingToasts={exitingToasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

// Toast Renderer
interface ToastRendererProps {
  toasts: Toast[]
  exitingToasts: Set<string>
  onRemove: (id: string) => void
}

const ToastRenderer: React.FC<ToastRendererProps> = ({ toasts, exitingToasts, onRemove }) => {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  const portalRoot = document.getElementById('toast-root') || document.body

  return createPortal(
    <ToastContainer>
      {toasts.map(toast => (
        <ToastItem
          key={toast.id}
          type={toast.type}
          isExiting={exitingToasts.has(toast.id)}
          role="alert"
          aria-live="polite"
        >
          <ToastIcon type={toast.type}>
            {getIcon(toast.type)}
          </ToastIcon>
          
          <ToastContent>
            <ToastMessage>{toast.message}</ToastMessage>
            {toast.action && (
              <ToastAction onClick={toast.action.onClick}>
                {toast.action.label}
              </ToastAction>
            )}
          </ToastContent>
          
          <ToastCloseButton
            onClick={() => onRemove(toast.id)}
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </ToastCloseButton>
          
          {!toast.persistent && toast.duration && (
            <ToastProgressBar duration={toast.duration} />
          )}
        </ToastItem>
      ))}
    </ToastContainer>,
    portalRoot
  )
}

// Convenience functions
export const toast = {
  info: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) => {
    // This will be implemented by the hook consumer
    throw new Error('toast.info() must be called within a ToastProvider')
  },
  success: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) => {
    throw new Error('toast.success() must be called within a ToastProvider')
  },
  warning: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) => {
    throw new Error('toast.warning() must be called within a ToastProvider')
  },
  error: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) => {
    throw new Error('toast.error() must be called within a ToastProvider')
  }
}

// Hook to create toast functions
export const useToastMethods = () => {
  const { addToast } = useToast()
  
  return {
    info: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) =>
      addToast({ message, type: 'info', ...options }),
    success: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) =>
      addToast({ message, type: 'success', ...options }),
    warning: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) =>
      addToast({ message, type: 'warning', ...options }),
    error: (message: string, options?: Partial<Omit<Toast, 'id' | 'message' | 'type'>>) =>
      addToast({ message, type: 'error', ...options })
  }
}