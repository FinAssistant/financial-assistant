import { FetchBaseQueryError } from '@reduxjs/toolkit/query'
import { SerializedError } from '@reduxjs/toolkit'

// Type definitions for common error formats
interface ErrorWithDetail {
  detail: string
}

interface ErrorWithMessage {
  message: string
}

interface BackendError {
  error: {
    message: string
    code?: string
  }
}

interface ValidationErrorItem {
  msg?: string
  message?: string
  detail?: string
}

interface FastApiValidationError {
  detail: ValidationErrorItem[]
}

// Type guards for error data structures
const hasDetail = (data: unknown): data is ErrorWithDetail => {
  return typeof data === 'object' && data !== null && 'detail' in data && typeof (data as ErrorWithDetail).detail === 'string'
}

const hasMessage = (data: unknown): data is ErrorWithMessage => {
  return typeof data === 'object' && data !== null && 'message' in data && typeof (data as ErrorWithMessage).message === 'string'
}

const hasBackendError = (data: unknown): data is BackendError => {
  return typeof data === 'object' && data !== null && 'error' in data && 
         typeof (data as BackendError).error === 'object' && 
         (data as BackendError).error !== null &&
         'message' in (data as BackendError).error &&
         typeof (data as BackendError).error.message === 'string'
}

const isFastApiValidationError = (data: unknown): data is FastApiValidationError => {
  return typeof data === 'object' && data !== null && 'detail' in data && 
         Array.isArray((data as FastApiValidationError).detail)
}

const isValidationErrorArray = (data: unknown): data is ValidationErrorItem[] => {
  return Array.isArray(data) && data.length > 0
}

const extractValidationErrorMessage = (item: ValidationErrorItem): string => {
  return item.msg || item.message || item.detail || String(item)
}

/**
 * Utility function to extract user-friendly error messages from RTK Query errors
 * Handles various error formats consistently across the application
 */
export const getErrorMessage = (error: FetchBaseQueryError | SerializedError | undefined): string => {
  if (!error) {
    return 'An unexpected error occurred'
  }

  // Handle network errors first (these have string status values)
  if ('status' in error && typeof error.status === 'string') {
    switch (error.status) {
      case 'FETCH_ERROR':
        return 'Network error. Please check your connection and try again.'
      case 'PARSING_ERROR':
        return 'Error processing server response. Please try again.'
      case 'TIMEOUT_ERROR':
        return 'Request timed out. Please try again.'
      case 'CUSTOM_ERROR':
        return 'A custom error occurred. Please try again.'
      default:
        return 'Request failed with error: ' + error
    }
  }

  // Handle RTK Query FetchBaseQueryError with data
  if ('data' in error && error.data) {
    const errorData = error.data

    // Check for standard error format with detail
    if (hasDetail(errorData)) {
      return errorData.detail
    }

    // Check for error object with message (our backend format)
    if (hasBackendError(errorData)) {
      return errorData.error.message
    }

    // Check for direct message
    if (hasMessage(errorData)) {
      return errorData.message
    }

    // Handle array of errors (validation errors)
    if (isValidationErrorArray(errorData)) {
      return errorData.map(extractValidationErrorMessage).join(', ')
    }

    // Handle FastAPI validation errors
    if (isFastApiValidationError(errorData)) {
      return errorData.detail.map(extractValidationErrorMessage).join(', ')
    }

    // Handle string error data
    if (typeof errorData === 'string') {
      return errorData
    }

    // If it's an object, try to stringify it as last resort
    if (typeof errorData === 'object' && errorData !== null) {
      const stringified = JSON.stringify(errorData)
      return stringified.length > 100 ? stringified.slice(0, 100) + '...' : stringified
    }

    return String(errorData)
  }

  // Handle SerializedError
  if ('message' in error && error.message) {
    return error.message
  }

  // Handle numeric status codes (HTTP status codes)
  if ('status' in error && typeof error.status === 'number') {
    return `Request failed with status: ${error.status}`
  }

  return 'An unexpected error occurred. Please try again.'
}

/**
 * Type guard to check if an error is a FetchBaseQueryError
 */
export const isFetchBaseQueryError = (error: unknown): error is FetchBaseQueryError => {
  return typeof error === 'object' && error !== null && 'status' in error
}

/**
 * Type guard to check if an error is a SerializedError
 */
export const isSerializedError = (error: unknown): error is SerializedError => {
  return typeof error === 'object' && error !== null && 'message' in error && !('status' in error)
}