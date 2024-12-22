import { Session } from 'next-auth';

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export class ChatService {
  private static baseUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat`;

  static async getSessions(session: Session): Promise<ChatSession[]> {
    if (!session?.access_token) {
      throw new Error('No access token available');
    }

    try {
      console.log('Fetching sessions from:', `${this.baseUrl}/sessions`);
      console.log('Using token:', session.access_token.substring(0, 10) + '...');

      const response = await fetch(`${this.baseUrl}/sessions`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        cache: 'no-store'
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Session fetch failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorText
        });
        throw new Error(`Server responded with ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Sessions fetched successfully:', data);
      return data;
    } catch (error) {
      console.error('GetSessions error:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch sessions');
    }
  }

  static async createSession(session: Session): Promise<ChatSession> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          title: 'New Chat',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Failed to create session: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.log('CreateSession error:', error);
      throw error;
    }
  }

  static async getMessages(
    session: Session,
    chatSessionId: number
  ): Promise<ChatMessage[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/sessions/${chatSessionId}/messages`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Failed to get messages: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.log('GetMessages error:', error);
      throw error;
    }
  }

  static async sendMessage(
    session: Session,
    chatSessionId: number,
    content: string
  ): Promise<ChatMessage> {
    if (!session?.access_token) {
      throw new Error('No access token available');
    }

    try {
      console.log('Sending message to session:', chatSessionId);
      
      const response = await fetch(
        `${this.baseUrl}/sessions/${chatSessionId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            role: 'USER',
            content,
          }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Message send failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorText
        });
        throw new Error(`Failed to send message: ${response.status}`);
      }

      const data = await response.json();
      console.log('Message sent and response received:', data);
      
      return await this.pollForResponse(session, chatSessionId, data.id);
    } catch (error) {
      console.error('SendMessage error:', error);
      throw error;
    }
  }

  private static async pollForResponse(
    authSession: Session,
    chatSessionId: number,
    messageId: number,
    maxAttempts = 30, // Maximum number of polling attempts
    interval = 1000 // Polling interval in milliseconds
  ): Promise<ChatMessage> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const response = await fetch(
        `${this.baseUrl}/sessions/${chatSessionId}/messages/${messageId}`,
        {
          headers: {
            'Authorization': `Bearer ${authSession.access_token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get message: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status === 'completed') {
        return data;
      }

      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('Timeout waiting for AI response');
  }

  static async deleteSession(
    session: Session,
    chatSessionId: number
  ): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/sessions/${chatSessionId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to delete chat session');
    }
  }

  static async getNewMessages(
    session: Session,
    chatSessionId: number,
    afterMessageId: number
  ): Promise<ChatMessage[]> {
    if (!session?.access_token) {
      throw new Error('No access token available');
    }

    try {
      const response = await fetch(
        `${this.baseUrl}/sessions/${chatSessionId}/messages?after=${afterMessageId}`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get new messages: ${response.status}`);
      }

      const data = await response.json();
      console.log('New messages received:', data);
      return data;
    } catch (error) {
      console.error('GetNewMessages error:', error);
      throw error;
    }
  }
} 