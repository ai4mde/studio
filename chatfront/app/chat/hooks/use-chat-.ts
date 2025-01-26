import { useState, useCallback, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { Message, ChatSession } from '@/app/chat/types';
import chatApi from '../api/chat-api';

interface ChatHookReturn {
  messages: Message[]
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
  handleSubmit: (e: React.FormEvent) => void
  isLoading: boolean
  isAiThinking: boolean
  stop: () => void
  reload: () => void
  error?: string
  sendMessage: (content: string) => Promise<void>
  resetChat: () => void
  startNewChat: (title: string) => Promise<void>
  isAuthenticated: boolean
  sessions: ChatSession[]
  selectChat: (sessionId: string) => Promise<void>
  currentSession: ChatSession | null
  deleteChat: () => Promise<void>
  progress?: number
  showLogoutWarning: boolean
  timeRemaining: number
  onContinueSession: () => void
}

const SESSION_TIMEOUT_DURATION = Number(process.env.NEXT_PUBLIC_SESSION_TIMEOUT_DURATION ?? 1800);   // 30 minutes in seconds
const SESSION_WARNING_THRESHOLD = Number(process.env.NEXT_PUBLIC_SESSION_WARNING_THRESHOLD ?? 120);    // Show warning when 2 minutes remain

export function useChat(): ChatHookReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [input, setInput] = useState('');
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [progress, setProgress] = useState<number>();
  const [showLogoutWarning, setShowLogoutWarning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(SESSION_TIMEOUT_DURATION);

  const { data: session, status } = useSession();
  const accessToken = session?.access_token;

  const isAuthenticated = status === 'authenticated' && !!accessToken;
  const isLoading = status === 'loading';

  useEffect(() => {
    if (!session) return;

    // Check session every 10 seconds
    const interval = setInterval(() => {
      const checkSession = async () => {
        try {
          const response = await fetch('/api/auth/session');
          const data = await response.json();
          
          if (data?.error === "RefreshAccessTokenError") {
            console.log('Session expired, logging out...');
            await signOut({ redirect: true, callbackUrl: '/login' });
          }
        } catch (error) {
          console.error('Session check failed:', error);
        }
      };
      
      checkSession();
    }, 10000); // 10 seconds

    return () => clearInterval(interval);
  }, [session]);

  // Force logout on session error
  useEffect(() => {
    if (session?.error === "RefreshAccessTokenError") {
      console.log('Session error detected, logging out...');
      signOut({ redirect: true, callbackUrl: '/login' });
    }
  }, [session?.error]);

  useEffect(() => {
    const loadSessions = async () => {
      if (!accessToken) return;
      try {
        const response = await chatApi.getSessions(accessToken);
        if (response.error) {
          setError(response.error);
          return;
        }
        setSessions(response.data || []);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to fetch sessions');
      }
    };
    loadSessions();
  }, [accessToken]);

  const selectChat = useCallback(async (sessionId: string) => {
    if (!accessToken) return;
    
    try {
      const session = sessions.find(s => s.id === sessionId);
      if (!session) throw new Error('Session not found');
      
      setCurrentSession(session);
      
      // Load messages and get initial progress
      const response = await chatApi.getMessages(sessionId, accessToken);
      if (response.error) throw new Error(response.error);
      
      if (response.data && response.data.length > 0) {
        const messages = response.data.map((msg) => ({
          id: msg.message_uuid || msg.id,
          content: msg.content,
          role: msg.role,
          created_at: msg.created_at,
          progress: msg.progress,
          message_uuid: msg.message_uuid
        }));
        
        setMessages(messages);
        
        // Find the latest assistant message with progress
        const latestAssistantMessage = [...messages]
          .reverse()
          .find(msg => msg.role === 'ASSISTANT' && msg.progress !== undefined);
        
        if (latestAssistantMessage?.progress !== undefined) {
          setProgress(latestAssistantMessage.progress);
        }
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to select chat');
    }
  }, [accessToken, sessions]);

  // Message handling
  const sendMessage = useCallback(async (content: string) => {
    if (!accessToken || !currentSession) {
      setError('No active chat session');
      return;
    }

    setIsAiThinking(true);
    setError(undefined);

    try {
      // Add user message
      const userMessage: Message = {
        id: crypto.randomUUID(),
        content,
        role: 'USER',
        created_at: new Date().toISOString(),
        progress: progress
      };
      
      setMessages(prev => [...prev, userMessage]);

      // Send to API and get AI response
      const messageResponse = await chatApi.sendMessage(
        accessToken,
        currentSession.id.toString(),
        content
      );

      if (messageResponse.error || !messageResponse.data) {
        throw new Error(messageResponse.error || 'No response data');
      }

      // Handle clear_messages flag from backend
      if (messageResponse.data.clear_messages) {
        setMessages([]);
        setProgress(0);
      }

      // Add AI response with progress
      const aiMessage: Message = {
        id: messageResponse.data.message_uuid,
        content: messageResponse.data.message,
        role: 'ASSISTANT',
        created_at: new Date().toISOString(),
        progress: messageResponse.data.progress
      };

      // Add the AI message to the chat
      setMessages(prev => [...prev, aiMessage]);

      // Update progress if provided
      if (messageResponse.data.progress !== undefined) {
        setProgress(messageResponse.data.progress);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsAiThinking(false);
    }
  }, [currentSession, accessToken, progress]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
    setInput('');
  };

  const stop = () => {
    setIsAiThinking(false);
  };

  const reload = () => {
    // Implement reload logic
  };

  const startNewChat = async (title: string) => {
    if (!accessToken) {
      setError('Not authenticated');
      return;
    }
    
    try {
      const response = await chatApi.createChatSession(title, accessToken);
      if (response.error) throw new Error(response.error);
      
      if (response.data) {
        setCurrentSession(response.data);
        setMessages([]); // Clear messages for new chat
        // Refresh sessions list
        const sessionsResponse = await chatApi.getSessions(accessToken);
        if (sessionsResponse.data) {
          setSessions(sessionsResponse.data);
        }
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create chat');
    }
  };

  const deleteChat = useCallback(async () => {
    if (!accessToken || !currentSession) {
      setError('No active chat session');
      return;
    }

    try {
      const response = await chatApi.deleteSession(accessToken, currentSession.id);
      if (response.error) throw new Error(response.error);

      // Clear current session, messages and progress
      setCurrentSession(null);
      setMessages([]);
      setProgress(undefined);

      // Refresh sessions list
      const sessionsResponse = await chatApi.getSessions(accessToken);
      if (sessionsResponse.data) {
        setSessions(sessionsResponse.data);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete chat');
    }
  }, [accessToken, currentSession]);

  // Timer effect
  useEffect(() => {
    if (!session || !isAuthenticated) return;
    
    setTimeRemaining(SESSION_TIMEOUT_DURATION);

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        const newTime = prev - 1;
        
        if (newTime === SESSION_WARNING_THRESHOLD) {
          setShowLogoutWarning(true);
        }
        
        if (newTime <= 0) {
          clearInterval(timer);
          signOut({ redirect: true, callbackUrl: '/login' });
        }
        
        return newTime;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [session, isAuthenticated]);

  // Reset timer function
  const resetInactivityTimer = useCallback(() => {
    setTimeRemaining(SESSION_TIMEOUT_DURATION);
    setShowLogoutWarning(false);
  }, []);

  // Reset on user activity
  useEffect(() => {
    if (session && isAuthenticated) {
      resetInactivityTimer();
    }
  }, [messages, input, session, isAuthenticated, resetInactivityTimer]);

  if (isLoading) {
    return {
      messages: [],
      input: '',
      handleInputChange: () => {},
      handleSubmit: () => {},
      isLoading: true,
      isAiThinking: false,
      stop: () => {},
      reload: () => {},
      error: undefined,
      sendMessage: async () => {},
      resetChat: () => {},
      startNewChat: async () => {},
      isAuthenticated: false,
      sessions: [],
      selectChat: async () => {},
      currentSession: null,
      deleteChat: async () => {},
      progress: undefined,
      showLogoutWarning: false,
      timeRemaining: SESSION_TIMEOUT_DURATION,
      onContinueSession: () => {},
    };
  }

  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    isAiThinking,
    stop,
    reload,
    error,
    sendMessage,
    resetChat: () => {
      setMessages([]);
      setCurrentSession(null);
    },
    startNewChat,
    isAuthenticated,
    sessions,
    selectChat,
    currentSession,
    deleteChat,
    progress,
    showLogoutWarning,
    timeRemaining,
    onContinueSession: resetInactivityTimer,
  };
}
