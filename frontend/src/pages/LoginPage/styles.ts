import styled, { keyframes } from 'styled-components'

export const Container = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, ${props => props.theme.colors.primary.main} 0%, ${props => props.theme.colors.secondary.main} 100%);
  padding: 20px;
`

export const FormContainer = styled.div`
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  min-width: 320px;
`

export const Title = styled.h1`
  text-align: center;
  margin-bottom: 30px;
  color: ${props => props.theme.colors.text.primary};
  font-size: 28px;
  font-weight: 600;
`

export const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`

export const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

export const Label = styled.label`
  font-weight: 500;
  color: ${props => props.theme.colors.text.primary};
  font-size: 14px;
`

export const Input = styled.input<{ $hasError?: boolean }>`
  padding: 12px 16px;
  border: 2px solid ${props => props.$hasError ? '#e74c3c' : props.theme.colors.border.light};
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: ${props => props.$hasError ? '#e74c3c' : props.theme.colors.primary.main};
    box-shadow: 0 0 0 3px ${props => props.$hasError ? 'rgba(231, 76, 60, 0.1)' : `${props.theme.colors.primary.main}20`};
  }
  
  &::placeholder {
    color: ${props => props.theme.colors.text.light};
  }
`

export const Button = styled.button`
  background: ${props => props.theme.colors.primary.main};
  color: white;
  border: none;
  padding: 14px 20px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 52px;
  
  &:hover:not(:disabled) {
    background: ${props => props.theme.colors.primary.dark};
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    background: ${props => props.theme.colors.text.light};
    cursor: not-allowed;
    transform: none;
  }
`

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`

export const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`

export const ErrorMessage = styled.div`
  color: #e74c3c;
  font-size: 14px;
  margin-top: 4px;
  padding: 8px 12px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 6px;
  border-left: 3px solid #e74c3c;
`

export const ToggleText = styled.p`
  text-align: center;
  margin-top: 20px;
  color: ${props => props.theme.colors.text.secondary};
  font-size: 14px;
`

export const ToggleLink = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme.colors.primary.main};
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  text-decoration: underline;
  
  &:hover {
    color: ${props => props.theme.colors.primary.dark};
  }
`

export const PasswordRequirements = styled.div`
  margin-top: 8px;
  padding: 12px;
  background: rgba(52, 152, 219, 0.1);
  border-radius: 6px;
  border-left: 3px solid ${props => props.theme.colors.primary.main};
  
  p {
    margin: 0 0 8px 0;
    font-size: 13px;
    font-weight: 600;
    color: ${props => props.theme.colors.text.secondary};
  }
  
  ul {
    margin: 0;
    padding-left: 16px;
    
    li {
      font-size: 12px;
      color: ${props => props.theme.colors.text.light};
      margin-bottom: 2px;
    }
  }
`