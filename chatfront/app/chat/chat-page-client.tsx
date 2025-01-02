'use client'

import { useChat } from "./hooks/use-chat"
import { ChatHeader } from "@/components/chat/chat-header"
import { ChatInput } from "@/components/chat/chat-input"
import { MessageList } from "@/components/chat/message-list"
import { NewChatDialog } from "@/components/chat/new-chat-dialog"
import { useState, useRef, useEffect, useCallback } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertMessageDialog } from '@/components/chat/alert-dialog'
import { signOut } from 'next-auth/react'
import { cn } from "@/lib/utils"

export default function ChatPageClient() {
  const { 
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
    onContinueSession
  } = useChat()

  const [isNewChatOpen, setIsNewChatOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messageListRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)

  // Add scroll handling
  const scrollToBottom = useCallback(() => {
    if (shouldAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [shouldAutoScroll])

  // Handle scroll events to detect if user has scrolled up
  const handleScroll = useCallback(() => {
    if (!messageListRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = messageListRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100

    setShouldAutoScroll(isAtBottom)
  }, [])

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleLogout = () => {
    signOut({ redirect: true, callbackUrl: '/login' })
  }

  const handleNewChat = () => {
    setIsNewChatOpen(true)
  }

  const handleSelectChat = (id: string) => {
    // TODO: Implement select chat
    console.log('Selected chat:', id)
  }

  const handleClearChat = () => {
    // Implement clear chat functionality
  }

  return (
    <>
      <div className={cn(
        "flex flex-col h-[calc(100vh-4rem)]",
        "bg-background/95 backdrop-blur",
        "supports-[backdrop-filter]:bg-background/60"
      )}>
        <ChatHeader 
          isLoading={isLoading} 
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onClearChat={handleClearChat}
          sessions={sessions}
          currentSession={currentSession}
        />
        
        <div 
          ref={messageListRef} 
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto"
        >
          <MessageList
            messages={messages}
            isLoading={isLoading}
            isEmpty={messages.length === 0}
            isAiThinking={isAiThinking}
          />
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-border bg-background/50">
          <ChatInput
            input={input}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            lastMessageId={messages[messages.length - 1]?.id}
            hasActiveSession={!!currentSession}
          />
          {error && (
            <Alert variant="destructive" className="mx-4 mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <NewChatDialog
          isOpen={isNewChatOpen}
          onClose={() => setIsNewChatOpen(false)}
          onCreateChat={startNewChat}
        />
      </div>

      <AlertMessageDialog
        isOpen={showLogoutWarning}
        onClose={handleLogout}
        onContinue={onContinueSession}
        title="Session Timeout Warning"
        message="Your session will expire soon due to inactivity."
        showContinue={true}
        countdownSeconds={timeRemaining}
      />
    </>
  )
} 