export interface Message {
  id: string;
  content: string;
  role: 'USER' | 'ASSISTANT';
  created_at: string;
  progress?: number;
  message_uuid?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  message: string;
  session_id: number;
  message_uuid: string;
  progress?: number;
}

export interface ChatMessage {
  id: string;
  content: string;
  role: string;
  created_at: string;
  message_uuid: string;
  progress?: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
} 