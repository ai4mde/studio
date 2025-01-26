import { ApiResponse, Message, ChatSession, MessageResponse } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiCallOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
}

export async function handleApiCall<T>(
  endpoint: string,
  accessToken: string,
  options: ApiCallOptions = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: options.method || 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { 
      error: error instanceof Error ? error.message : 'An unknown error occurred' 
    };
  }
}

const ensureValidToken = (token: string | undefined): string => {
  if (!token) {
    throw new Error('No access token provided');
  }
  const cleanToken = token.replace(/^Bearer\s+/i, '');
  return `Bearer ${cleanToken}`;
};

const handleUnauthorized = async () => {
  // Redirect to login page directly
  window.location.href = '/login';
};

const handleApiError = async (error: unknown, defaultMessage: string) => {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return { error: 'Network error - please check your connection' };
  }

  // Check for 401 response
  if (error instanceof Response) {
    if (error.status === 401) {
      await handleUnauthorized();
      return { error: 'Session expired - please sign in again' };
    }
    const errorText = await error.text();
    return { error: `API error: ${error.status} ${errorText}` };
  }

  console.error(defaultMessage, error);
  return { error: defaultMessage };
};

const createApiHeaders = (accessToken: string) => ({
  'Authorization': ensureValidToken(accessToken),
  'Accept': 'application/json',
  'Content-Type': 'application/json',
});

export const chatApi = {
  getSessions: async (accessToken: string): Promise<ApiResponse<ChatSession[]>> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/sessions`, {
        method: 'GET',
        headers: createApiHeaders(accessToken),
      });

      if (!response.ok) throw response;
      const data = await response.json();
      return { data };
    } catch (error) {
      return handleApiError(error, 'Failed to fetch chat sessions');
    }
  },

  createSession: async (accessToken: string, title?: string): Promise<ApiResponse<ChatSession>> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/sessions`, {
        method: 'POST',
        headers: createApiHeaders(accessToken),
        body: JSON.stringify({ 
          title: title || 'New Chat'  // Use provided title or default
        })
      });

      if (!response.ok) throw response;
      const data = await response.json();
      return { data };
    } catch (error) {
      return handleApiError(error, 'Failed to create chat session');
    }
  },

  getMessages: async (sessionId: string, accessToken: string): Promise<ApiResponse<Message[]>> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/chat/${sessionId}`, {
        method: 'GET',
        headers: createApiHeaders(accessToken),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch messages' };
    }
  },

  sendMessage: async (accessToken: string, sessionId: string, content: string): Promise<ApiResponse<MessageResponse>> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/chat/${sessionId}`, {
        method: 'POST',
        headers: createApiHeaders(accessToken),
        body: JSON.stringify({
          content,
          session_id: sessionId.toString(),
          message_uuid: null
        })
      });

      if (!response.ok) throw response;
      const data = await response.json();
      return { data };
    } catch (error) {
      return handleApiError(error, 'Failed to send message');
    }
  },

  deleteSession: async (accessToken: string, sessionId: string): Promise<ApiResponse<void>> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: createApiHeaders(accessToken),
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      return { data: undefined };
    } catch (error) {
      console.error('Failed to delete session:', error);
      return { error: error instanceof Error ? error.message : 'Failed to delete session' };
    }
  },
};

export default chatApi;
