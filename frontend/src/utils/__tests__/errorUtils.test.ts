import { getErrorMessage, isFetchBaseQueryError, isSerializedError } from '../errorUtils'
import { FetchBaseQueryError } from '@reduxjs/toolkit/query'
import { SerializedError } from '@reduxjs/toolkit'

describe('errorUtils', () => {
  describe('getErrorMessage', () => {
    it('should return default message for undefined error', () => {
      expect(getErrorMessage(undefined)).toBe('An unexpected error occurred')
    })

    describe('FetchBaseQueryError handling', () => {
      it('should extract detail from error.data.detail', () => {
        const error: FetchBaseQueryError = {
          status: 400,
          data: {
            detail: 'Invalid credentials provided'
          }
        }
        expect(getErrorMessage(error)).toBe('Invalid credentials provided')
      })

      it('should extract message from error.data.error.message (backend format)', () => {
        const error: FetchBaseQueryError = {
          status: 400,
          data: {
            error: {
              message: 'Authentication failed',
              code: 'AUTH_ERROR'
            }
          }
        }
        expect(getErrorMessage(error)).toBe('Authentication failed')
      })

      it('should extract message from error.data.message', () => {
        const error: FetchBaseQueryError = {
          status: 500,
          data: {
            message: 'Internal server error'
          }
        }
        expect(getErrorMessage(error)).toBe('Internal server error')
      })

      it('should handle array of errors', () => {
        const error: FetchBaseQueryError = {
          status: 422,
          data: [
            { message: 'Email is required' },
            { message: 'Password is too short' }
          ]
        }
        expect(getErrorMessage(error)).toBe('Email is required, Password is too short')
      })

      it('should handle FastAPI validation errors', () => {
        const error: FetchBaseQueryError = {
          status: 422,
          data: {
            detail: [
              { msg: 'field required', field: 'email' },
              { msg: 'ensure this value has at least 8 characters', field: 'password' }
            ]
          }
        }
        expect(getErrorMessage(error)).toBe('field required, ensure this value has at least 8 characters')
      })

      it('should stringify complex objects as fallback', () => {
        const error: FetchBaseQueryError = {
          status: 400,
          data: {
            complexField: 'value',
            anotherField: 123
          }
        }
        const result = getErrorMessage(error)
        expect(result).toContain('complexField')
        expect(result).toContain('anotherField')
        expect(result.length).toBeLessThanOrEqual(103) // 100 chars + '...'
      })

      it('should handle string data', () => {
        const error: FetchBaseQueryError = {
          status: 400,
          data: 'Simple error message'
        }
        expect(getErrorMessage(error)).toBe('Simple error message')
      })

      it('should handle network errors', () => {
        // FETCH_ERROR - network connectivity issues
        const fetchError: FetchBaseQueryError = {
          status: 'FETCH_ERROR',
          data: undefined,
          error: 'Failed to fetch'
        }
        expect(getErrorMessage(fetchError)).toBe('Network error. Please check your connection and try again.')

        // TIMEOUT_ERROR - request timeout
        const timeoutError: FetchBaseQueryError = {
          status: 'TIMEOUT_ERROR', 
          data: undefined,
          error: 'Request timeout'
        }
        expect(getErrorMessage(timeoutError)).toBe('Request timed out. Please try again.')

        // PARSING_ERROR - response parsing failed
        const parsingError: FetchBaseQueryError = {
          status: 'PARSING_ERROR',
          originalStatus: 200,
          data: "undefined", 
          error: 'JSON parse error'
        }
        expect(getErrorMessage(parsingError)).toBe('Error processing server response. Please try again.')

        // CUSTOM_ERROR - custom error
        const customError: FetchBaseQueryError = {
          status: 'CUSTOM_ERROR',
          data: undefined,
          error: 'Custom error occurred'
        }
        expect(getErrorMessage(customError)).toBe('A custom error occurred. Please try again.')
      })

      it('should handle numeric status codes', () => {
        const error: FetchBaseQueryError = {
          status: 500,
          data: null
        }
        expect(getErrorMessage(error)).toBe('Request failed with status: 500')
      })
    })

    describe('SerializedError handling', () => {
      it('should extract message from SerializedError', () => {
        const error: SerializedError = {
          message: 'Redux toolkit error message',
          name: 'SerializedError'
        }
        expect(getErrorMessage(error)).toBe('Redux toolkit error message')
      })

      it('should handle SerializedError without message', () => {
        const error: SerializedError = {
          name: 'SerializedError'
        }
        expect(getErrorMessage(error)).toBe('An unexpected error occurred. Please try again.')
      })
    })

    describe('edge cases', () => {
      it('should handle empty object', () => {
        const error = {}
        expect(getErrorMessage(error)).toBe('An unexpected error occurred. Please try again.')
      })

      it('should handle error with data but no recognizable format', () => {
        const error: FetchBaseQueryError = {
          status: 400,
          data: {
            randomField: 'random value'
          }
        }
        const result = getErrorMessage(error)
        expect(result).toContain('randomField')
      })

      it('should handle very long error messages', () => {
        const longMessage = 'x'.repeat(200)
        const error: FetchBaseQueryError = {
          status: 400,
          data: {
            someComplexObject: longMessage
          }
        }
        const result = getErrorMessage(error)
        expect(result.length).toBeLessThanOrEqual(103) // Should be truncated
        expect(result).toContain('...')
      })
    })
  })

  describe('isFetchBaseQueryError', () => {
    it('should return true for FetchBaseQueryError', () => {
      const error: FetchBaseQueryError = {
        status: 400,
        data: { detail: 'error' }
      }
      expect(isFetchBaseQueryError(error)).toBe(true)
    })

    it('should return true for network error', () => {
      const error = {
        status: 'FETCH_ERROR',
        data: undefined,
        error: 'Network error'
      }
      expect(isFetchBaseQueryError(error)).toBe(true)
    })

    it('should return false for SerializedError', () => {
      const error: SerializedError = {
        message: 'error',
        name: 'SerializedError'
      }
      expect(isFetchBaseQueryError(error)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isFetchBaseQueryError(undefined)).toBe(false)
    })

    it('should return false for null', () => {
      expect(isFetchBaseQueryError(null)).toBe(false)
    })

    it('should return false for plain object without status', () => {
      expect(isFetchBaseQueryError({ message: 'error' })).toBe(false)
    })
  })

  describe('isSerializedError', () => {
    it('should return true for SerializedError', () => {
      const error: SerializedError = {
        message: 'error',
        name: 'SerializedError'
      }
      expect(isSerializedError(error)).toBe(true)
    })

    it('should return false for FetchBaseQueryError', () => {
      const error: FetchBaseQueryError = {
        status: 400,
        data: { detail: 'error' }
      }
      expect(isSerializedError(error)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isSerializedError(undefined)).toBe(false)
    })

    it('should return false for null', () => {
      expect(isSerializedError(null)).toBe(false)
    })

    it('should return false for object without message', () => {
      expect(isSerializedError({ status: 400 })).toBe(false)
    })

    it('should return true for object with message but no status', () => {
      expect(isSerializedError({ message: 'error' })).toBe(true)
    })
  })
})