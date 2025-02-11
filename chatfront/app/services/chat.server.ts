import type { ChatSession, Message } from "../types/chat.types";

const API_URL = "http://localhost:8000/api/v1";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
  if (!response.ok) {
    const error = await response.json().catch(() => null);
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
  async getSessions(accessToken: string): Promise<ApiResponse<ChatSession[]>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json'
        }
      });
      return handleResponse<ChatSession[]>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to fetch sessions'
      };
    }
  },

  async getSession(accessToken: string, sessionId: number): Promise<ApiResponse<ChatSession>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json'
        }
      });
      return handleResponse<ChatSession>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to fetch session'
      };
    }
  },

  async createChatSession(title: string, accessToken: string): Promise<ApiResponse<ChatSession>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ title })
      });
      return handleResponse<ChatSession>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to create session'
      };
    }
  },

  async deleteSession(accessToken: string, sessionId: number): Promise<ApiResponse<void>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json'
        }
      });
      return handleResponse<void>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to delete session'
      };
    }
  },

  async sendMessage(
    accessToken: string, 
    sessionId: number, 
    content: string
  ): Promise<ApiResponse<Message>> {
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ content })
      });
      return handleResponse<Message>(response);
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to send message'
      };
    }
  }
}; 