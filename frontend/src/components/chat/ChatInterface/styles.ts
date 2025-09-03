import styled from 'styled-components'

export const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 500px;
  max-height: 500px;
  background: ${({ theme }) => theme.colors.background.card};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
  border-radius: ${({ theme }) => theme.radii.card};
  box-shadow: ${({ theme }) => theme.shadows.card};
  overflow: hidden;

  @media (min-width: ${({ theme }) => theme.breakpoints.md}) {
    height: 600px;
    max-height: 600px;
  }
`

export const ChatHeader = styled.div`
  padding: ${({ theme }) => theme.spacing[4]};
  background: ${({ theme }) => theme.colors.background.secondary};
  border-bottom: 1px solid ${({ theme }) => theme.colors.border.light};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing[2]};
`

export const ChatTitle = styled.h3`
  margin: 0;
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: ${({ theme }) => theme.fontWeights.semibold};
  color: ${({ theme }) => theme.colors.text.primary};
  font-family: ${({ theme }) => theme.fonts.heading};
`

// Styled wrapper for Assistant UI Thread component
export const StyledThreadContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* Allow flex child to shrink */

  /* Ensure ThreadPrimitive.Root takes full height and uses flexbox */
  [data-thread-root],
  .thread-root {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }

  /* Ensure ThreadPrimitive.Viewport is scrollable and takes available space */
  [data-thread-viewport],
  .thread-viewport {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    min-height: 0;
  }
  
  /* Apply theme styling to Assistant UI components using data attributes */
  [data-message-role="user"] {
    [data-message-content] {
      background: ${({ theme }) => theme.colors.primary.main};
      color: ${({ theme }) => theme.colors.text.inverse};
      border-radius: ${({ theme }) => `${theme.radii.xl} ${theme.radii.xl} ${theme.radii.base} ${theme.radii.xl}`};
      padding: ${({ theme }) => theme.spacing[3]} ${({ theme }) => theme.spacing[4]};
      margin-left: auto;
      max-width: 85%;
      box-shadow: ${({ theme }) => theme.shadows.sm};
    }
  }

  [data-message-role="assistant"] {
    [data-message-content] {
      background: ${({ theme }) => theme.colors.background.secondary};
      color: ${({ theme }) => theme.colors.text.primary};
      border-radius: ${({ theme }) => `${theme.radii.xl} ${theme.radii.xl} ${theme.radii.xl} ${theme.radii.base}`};
      padding: ${({ theme }) => theme.spacing[3]} ${({ theme }) => theme.spacing[4]};
      margin-right: auto;
      max-width: 85%;
      box-shadow: ${({ theme }) => theme.shadows.sm};
    }
  }

  /* Ensure composer is visible and styled */
  [data-composer-root],
  .composer-root {
    padding: ${({ theme }) => theme.spacing[4]};
    border-top: 1px solid ${({ theme }) => theme.colors.border.light};
    background: ${({ theme }) => theme.colors.background.primary};
    display: flex;
    gap: ${({ theme }) => theme.spacing[2]};
    align-items: flex-end;
    flex-shrink: 0; /* Prevent composer from shrinking */
    margin-top: auto; /* Push composer to bottom */
  }

  [data-composer-input],
  .composer-input,
  [role="textbox"],
  textarea[placeholder*="finances"] {
    flex: 1 !important;
    min-height: 40px !important;
    max-height: 120px !important;
    padding: ${({ theme }) => theme.spacing[2]} ${({ theme }) => theme.spacing[3]} !important;
    border: 1px solid ${({ theme }) => theme.colors.border.light} !important;
    border-radius: ${({ theme }) => theme.radii.input} !important;
    font-family: ${({ theme }) => theme.fonts.primary} !important;
    font-size: ${({ theme }) => theme.fontSizes.base} !important;
    line-height: ${({ theme }) => theme.lineHeights.normal} !important;
    resize: none !important;
    outline: none !important;
    transition: ${({ theme }) => theme.transitions.normal} !important;
    background: ${({ theme }) => theme.colors.background.primary} !important;
    color: ${({ theme }) => theme.colors.text.primary} !important;
    
    &:focus {
      border-color: ${({ theme }) => theme.colors.border.focus} !important;
      box-shadow: 0 0 0 2px ${({ theme }) => theme.colors.primary[100]} !important;
    }

    &::placeholder {
      color: ${({ theme }) => theme.colors.text.muted} !important;
    }
  }

  [data-composer-send],
  .composer-send,
  .composer-root button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 40px !important;
    height: 40px !important;
    border: none !important;
    border-radius: ${({ theme }) => theme.radii.base} !important;
    background: ${({ theme }) => theme.colors.primary.main} !important;
    color: ${({ theme }) => theme.colors.text.inverse} !important;
    cursor: pointer !important;
    transition: ${({ theme }) => theme.transitions.normal} !important;
    
    &:hover:not(:disabled) {
      background: ${({ theme }) => theme.colors.primary.dark} !important;
    }

    &:disabled {
      background: ${({ theme }) => theme.colors.border.medium} !important;
      cursor: not-allowed !important;
    }

    svg {
      width: 16px !important;
      height: 16px !important;
    }
  }

  /* Ensure messages container has proper scrolling */
  [data-message-container],
  [data-thread-messages] {
    flex: 1;
    overflow-y: auto;
    padding: ${({ theme }) => theme.spacing[2]};
    display: flex;
    flex-direction: column;
    gap: ${({ theme }) => theme.spacing[3]};
    min-height: 0; /* Allow scrolling */

    /* Custom scrollbar styling */
    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: ${({ theme }) => theme.colors.background.secondary};
    }

    &::-webkit-scrollbar-thumb {
      background: ${({ theme }) => theme.colors.border.medium};
      border-radius: ${({ theme }) => theme.radii.full};
    }

    &::-webkit-scrollbar-thumb:hover {
      background: ${({ theme }) => theme.colors.border.dark};
    }
  }
`