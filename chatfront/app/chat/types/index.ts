import { Session } from "next-auth";

export interface Message {
  id: string;
  content: string;
  role: 'USER' | 'ASSISTANT';
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface ChatContextType {
  messages: Message[];
  isAiThinking: boolean;
  error: string | null;
  session: Session | null;
  existingSessions: ChatSession[];
  currentSessionId: string | null;
}

export interface ChatInputProps {
  onSubmit: (message: string) => Promise<void>;
  disabled: boolean;
  placeholder?: string;
}

export interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export interface ChatDialogsProps {
  onReset: () => void;
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
  error?: string;
}

export interface MessageResponse {
  message: string;
  session_id: number;
  message_uuid: string;
}

export interface CreateSessionResponse {
  id: string;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  messages: Message[];
}
