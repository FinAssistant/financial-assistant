import React from 'react';
import { PlaidLinkOnEvent, PlaidLinkOnExit, PlaidLinkOnSuccess, usePlaidLink } from 'react-plaid-link';
import styled from 'styled-components';
import { AlertCircle, ExternalLink } from 'lucide-react';

interface PlaidConnectProps {
  linkToken: string;
  onSuccess: PlaidLinkOnSuccess;
  onEvent: PlaidLinkOnEvent;
  onExit: PlaidLinkOnExit;
}

const PlaidConnectContainer = styled.div`
  margin: ${({ theme }) => theme.spacing.md} 0;
  padding: ${({ theme }) => theme.spacing.md};
  background: ${({ theme }) => theme.colors.background.secondary};
  border-radius: ${({ theme }) => theme.radii.lg};
  border: 1px solid ${({ theme }) => theme.colors.border.light};
`;

const ConnectButton = styled.button`
  width: 100%;
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.lg};
  background: ${({ theme }) => theme.colors.primary.main};
  color: white;
  border: none;
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${({ theme }) => theme.spacing.sm};

  &:hover:not(:disabled) {
    background: ${({ theme }) => theme.colors.primary.dark};
    transform: translateY(-1px);
  }

  &:disabled {
    background: ${({ theme }) => theme.colors.neutral.main};
    cursor: not-allowed;
    transform: none;
  }

  &:active {
    transform: translateY(0);
  }
`;

const ErrorMessage = styled.div`
  margin-top: ${({ theme }) => theme.spacing.sm};
  padding: ${({ theme }) => theme.spacing.sm};
  background: ${({ theme }) => theme.colors.loss.main}10;
  color: ${({ theme }) => theme.colors.loss.main};
  border: 1px solid ${({ theme }) => theme.colors.loss.main}20;
  border-radius: ${({ theme }) => theme.radii.sm};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.xs};
`;

const SecurityNote = styled.div`
  margin-top: ${({ theme }) => theme.spacing.sm};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text.secondary};
  text-align: center;
`;

export const PlaidConnect: React.FC<PlaidConnectProps> = ({
  linkToken,
  onSuccess,
  onEvent,
  onExit
}) => {
  
  const { open, ready, error } = usePlaidLink({
    token: linkToken,
    onSuccess,
    onEvent,
    onExit
  });

  const handleClick = () => {
    if (ready) {
      open();
    }
  };

  return (
    <PlaidConnectContainer>
      <ConnectButton
        onClick={handleClick}
        disabled={!ready}
        type="button"
      >
        <ExternalLink size={16} />
        {ready ? "Connect Your Accounts" : "Preparing connection..."}
      </ConnectButton>

      {error && (
        <ErrorMessage>
          <AlertCircle size={16} />
          Connection error: {error.message}
        </ErrorMessage>
      )}

      <SecurityNote>
        🔒 Your data is protected with bank-level security
      </SecurityNote>
    </PlaidConnectContainer>
  );
};