import type { ChatSession, Message, MessageResponse } from "../types/chat.types";
import type { CustomUser } from "../types/auth.types";

const API_URL = "http://localhost:8000/api/v1";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

function getAuthHeader(user: CustomUser): string {
  const tokenType = user.token_type.charAt(0).toUpperCase() + user.token_type.slice(1).toLowerCase();
  return `${tokenType} ${user.access_token}`;
}

async function handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    
    // Handle authentication errors
    if (response.status === 401 || error?.detail === "Could not validate credentials") {
      window.location.href = `/login?redirectTo=${window.location.pathname}`;
      return { error: "Session expired. Please log in again." };
    }
    
    return {
      error: error?.detail || `API error: ${response.status} ${response.statusText}`
    };
  }

  try {
    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      error: 'Failed to parse response'
    };
  }
}

export const chatApi = {
  async getSessions(user: CustomUser): Promise<ApiResponse<ChatSession[]>> {
    try {
      console.log('Auth header:', getAuthHeader(user));
      const response = await fetch(`${API_URL}/chat/sessions`, {
        headers: {
          'Authorization': getAuthHeader(user),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });
      return handleResponse<ChatSession[]>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to fetch sessions'
      };
    }
  },

  async getSession(user: CustomUser, sessionId: number): Promise<ApiResponse<ChatSession>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: {
          'Authorization': getAuthHeader(user),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });
      return handleResponse<ChatSession>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to fetch session'
      };
    }
  },

  async createChatSession(title: string, user: CustomUser): Promise<ApiResponse<ChatSession>> {
    try {
      console.log('Creating chat session with title:', title);
      console.log('Auth header:', getAuthHeader(user));
      
      const response = await fetch(`${API_URL}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': getAuthHeader(user),
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        mode: 'cors',
        body: JSON.stringify({ title })
      });

      console.log('Response status:', response.status);
      const responseText = await response.text();
      console.log('Response text:', responseText);

      if (!response.ok) {
        return {
          error: `Failed to create chat session: ${response.status} ${response.statusText}\n${responseText}`
        };
      }

      try {
        const data = JSON.parse(responseText);
        return { data };
      } catch (error) {
        console.error('Failed to parse response:', error);
        return {
          error: 'Failed to parse server response'
        };
      }
    } catch (error) {
      console.error('Failed to create chat session:', error);
      return {
        error: error instanceof Error ? error.message : 'Failed to create session'
      };
    }
  },

  async deleteSession(user: CustomUser, sessionId: number): Promise<ApiResponse<void>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': getAuthHeader(user),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });
      return handleResponse<void>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to delete session'
      };
    }
  },

  async sendMessage(
    user: CustomUser,
    sessionId: number,
    content: string
  ): Promise<ApiResponse<Message>> {
    try {
      const message_uuid = crypto.randomUUID();
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': getAuthHeader(user),
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        mode: 'cors',
        body: JSON.stringify({ content, message_uuid })
      });

      const apiResponse = await handleResponse<MessageResponse>(response);
      
      if (apiResponse.error) {
        return { error: apiResponse.error };
      }
      if (!apiResponse.data) {
        return { error: 'No data received from server' };
      }

      // Convert MessageResponse to Message
      const message: Message = {
        id: apiResponse.data.message_uuid,
        role: 'ASSISTANT',
        content: apiResponse.data.message,
        created_at: new Date().toISOString(),
        message_uuid: apiResponse.data.message_uuid,
        progress: apiResponse.data.progress
      };

      return { data: message };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to send message'
      };
    }
  },

  async getMessages(user: CustomUser, sessionId: number): Promise<ApiResponse<Message[]>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        headers: {
          'Authorization': getAuthHeader(user),
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });

      const apiResponse = await handleResponse<Message[]>(response);
      if (apiResponse.error) {
        return { error: apiResponse.error };
      }
      if (!apiResponse.data) {
        return { error: 'No messages received from server' };
      }

      return { data: apiResponse.data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to fetch messages'
      };
    }
  }
}; 