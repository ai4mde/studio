export interface ChatSession {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string | null;
  messages: Message[];
}

export interface Message {
  id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  created_at: string;
  message_uuid?: string;
  progress?: number;
}

export interface MessageResponse {
  message: string;
  session_id: number;
  message_uuid: string;
  progress?: number;
}

export enum ChatRole {
  USER = 'USER',
  ASSISTANT = 'ASSISTANT',
  SYSTEM = 'SYSTEM'
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  input: string;
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  progress?: number;
  isAiThinking: boolean;
} 