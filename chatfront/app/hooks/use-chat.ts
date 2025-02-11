import { useState, useCallback, useEffect } from 'react';
import type { ChatSession, Message, ChatState } from '../types/chat.types';
import { chatApi } from '../services/chat';
import { useUser } from './use-user';

interface ChatHookReturn extends ChatState {
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  startNewChat: (title: string) => Promise<void>;
  deleteChat: () => Promise<void>;
  selectChat: (sessionId: number) => Promise<void>;
  stop: () => void;
  reload: () => void;
}

export function useChat(): ChatHookReturn {
  const user = useUser();

  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    input: '',
    sessions: [],
    currentSession: null,
    progress: undefined,
    isAiThinking: false
  });

  const setPartialState = (newState: Partial<ChatState>) => {
    setState(prev => ({ ...prev, ...newState }));
  };

  // Load sessions on mount
  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  const loadSessions = async () => {
    if (!user) return;

    try {
      const response = await chatApi.getSessions(user);
      if (response.error) throw new Error(response.error);
      if (response.data) {
        setPartialState({ sessions: response.data });
      }
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : 'Failed to load sessions'
      });
    }
  };

  const selectChat = async (sessionId: number) => {
    if (!user) {
      setPartialState({ error: 'Not authenticated' });
      return;
    }

    try {
      // Get session details
      const sessionResponse = await chatApi.getSession(user, sessionId);
      if (sessionResponse.error) throw new Error(sessionResponse.error);
      if (!sessionResponse.data) throw new Error('No session data received');

      // Get messages for the session
      const messagesResponse = await chatApi.getMessages(user, sessionId);
      if (messagesResponse.error) throw new Error(messagesResponse.error);
      
      // Get progress from the last message if available
      const messages = messagesResponse.data || [];
      const lastMessage = messages[messages.length - 1];
      const progress = lastMessage?.progress;

      setPartialState({
        currentSession: sessionResponse.data,
        messages: messages,
        progress: progress,
        error: null
      });
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : 'Failed to load chat session'
      });
    }
  };

  const sendMessage = async (content: string) => {
    if (!user || !state.currentSession) {
      setPartialState({ error: 'No active chat session' });
      return;
    }

    try {
      // Add user message to the UI immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'USER',
        content,
        created_at: new Date().toISOString(),
        progress: state.progress
      };

      // First update: Show user message
      setPartialState({
        messages: [...state.messages, userMessage]
      });

      // Second update: Show AI thinking state
      setPartialState({
        isLoading: true,
        error: null,
        isAiThinking: true
      });

      // Send message to API
      const response = await chatApi.sendMessage(
        user,
        state.currentSession.id,
        content
      );

      if (response.error) {
        if (response.error === "Session expired. Please log in again.") {
          setPartialState({
            messages: [],
            currentSession: null,
            sessions: [],
            error: response.error
          });
          return;
        }
        throw new Error(response.error);
      }
      
      if (response.data) {
        // Update with AI response
        setPartialState({
          messages: [...state.messages, userMessage, response.data],
          progress: response.data.progress
        });
      }
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : 'Failed to send message'
      });
    } finally {
      setPartialState({ isLoading: false, isAiThinking: false });
    }
  };

  const startNewChat = async (title: string) => {
    if (!user) {
      setPartialState({ error: 'Not authenticated' });
      return;
    }
    
    try {
      const response = await chatApi.createChatSession(title, user);
      if (response.error) throw new Error(response.error);
      
      if (response.data) {
        setPartialState({
          currentSession: response.data,
          messages: [],
          progress: undefined
        });
        await loadSessions();
      }
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : 'Failed to create chat'
      });
    }
  };

  const deleteChat = useCallback(async () => {
    if (!user || !state.currentSession) {
      setPartialState({ error: 'No active chat session' });
      return;
    }

    try {
      const response = await chatApi.deleteSession(user, state.currentSession.id);
      if (response.error) throw new Error(response.error);

      setPartialState({
        currentSession: null,
        messages: [],
        progress: undefined
      });

      await loadSessions(); // Refresh sessions list
    } catch (error) {
      setPartialState({
        error: error instanceof Error ? error.message : 'Failed to delete chat'
      });
    }
  }, [user, state.currentSession]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPartialState({ input: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (state.input.trim()) {
      sendMessage(state.input);
      setPartialState({ input: '' });
    }
  };

  const stop = () => {
    setPartialState({ isAiThinking: false });
  };

  const reload = () => {
    // Implement reload functionality if needed
  };

  return {
    ...state,
    handleInputChange,
    handleSubmit,
    startNewChat,
    deleteChat,
    selectChat,
    stop,
    reload
  };
} 