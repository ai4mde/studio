import { useState, useCallback, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Message, ChatSession } from '../types'
import { chatApi } from '../api/chat-api'

export function useChat() {
  const { data: session } = useSession()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isAiThinking, setIsAiThinking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)
  const [showLogoutWarning, setShowLogoutWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(0)

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !currentSession?.id || !session?.user?.accessToken) return

    try {
      setIsLoading(true)
      setIsAiThinking(true)
      
      const newMessage: Message = {
        id: Date.now().toString(),
        content: input.trim(),
        role: 'USER',
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, newMessage])
      setInput('')
      
      const result = await chatApi.sendMessage(
        session.user.accessToken, 
        currentSession.id.toString(),
        input.trim()
      )

      if (result.error) {
        setError(result.error)
        return
      }

      if (result.data) {
        const aiMessage: Message = {
          id: result.data.message_uuid,
          content: result.data.message,
          role: 'ASSISTANT',
          created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev, aiMessage])
      }
    } catch (err) {
      setError('Failed to send message')
      console.error('Error sending message:', err)
    } finally {
      setIsLoading(false)
      setIsAiThinking(false)
    }
  }, [input, currentSession, session])

  const startNewChat = useCallback(async (title?: string) => {
    if (!session?.user?.accessToken) {
      setError('No authentication token found')
      return
    }

    try {
      setIsLoading(true)
      const result = await chatApi.createSession(session.user.accessToken, title)
      
      if (result.error || !result.data) {
        throw new Error(result.error || 'Failed to create session')
      }

      setSessions(prev => [result.data!, ...prev])
      setCurrentSession(result.data)
      setMessages([])
    } catch (err) {
      setError('Failed to create new chat')
      console.error('Error creating new chat:', err)
    } finally {
      setIsLoading(false)
    }
  }, [session])

  const onContinueSession = useCallback(() => {
    setShowLogoutWarning(false)
  }, [])

  const selectChat = useCallback(async (sessionId: string) => {
    try {
      const session = sessions.find(s => s.id === sessionId)
      if (session) {
        setCurrentSession(session)
        setMessages([]) // Clear current messages
        // TODO: Fetch messages for this session if needed
      }
    } catch (err) {
      setError('Failed to select chat')
    }
  }, [sessions])

  const deleteChat = useCallback(async (sessionId: string) => {
    if (!session?.user?.accessToken) return;
    
    try {
      const result = await chatApi.deleteSession(session.user.accessToken, sessionId);
      if (result.error) throw new Error(result.error);
      
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      setError('Failed to delete chat');
    }
  }, [currentSession, session]);

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (showLogoutWarning) {
      const countdown = 60 // 60 seconds warning
      setTimeRemaining(countdown)
      timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [showLogoutWarning])

  // Load sessions when authenticated
  useEffect(() => {
    if (session?.user?.accessToken) {
      chatApi.getSessions(session.user.accessToken)
        .then(result => {
          if (result.data) {
            setSessions(result.data)
          }
        })
        .catch(err => {
          console.error('Failed to load sessions:', err)
          setError('Failed to load chat sessions')
        })
    }
  }, [session])

  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    isAiThinking,
    error,
    startNewChat,
    sessions,
    currentSession,
    showLogoutWarning,
    timeRemaining,
    onContinueSession,
    selectChat,
    deleteChat,
    progress: 0,
  }
}