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
}

export enum ChatRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
} 