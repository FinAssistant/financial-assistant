export interface PlaidLinkData {
  status: string;
  link_token: string;
  expiration: string;
  request_id: string;
}

/**
 * Extract guidance text before JSON data in a message
 */
export const extractGuidanceText = (content: string): string => {
  // Extract guidance text before JSON data
  const jsonStart = content.indexOf('{"');
  if (jsonStart > 0) {
    return content.substring(0, jsonStart).trim();
  }
  return content;
};

/**
 * Check if message content contains Plaid link data
 */
export const isPlaidMessage = (content: string): boolean => {
  return content.includes('link_token') && content.includes('status');
};

/**
 * Extract Plaid link data from message content
 */
export const extractPlaidData = (content: string): PlaidLinkData | null => {
  try {
    // Look for JSON containing link_token
    const jsonMatch = content.match(/\{[^}]*"link_token"[^}]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (e) {
    console.warn('Failed to parse Plaid data from message:', e);
  }
  return null;
};

/**
 * Parse message content for Plaid data (combines check and extract)
 */
export const parseMessageForPlaidData = (content: string): PlaidLinkData | null => {
  if (!isPlaidMessage(content)) {
    return null;
  }
  return extractPlaidData(content);
};