'use client'

import { useState } from 'react'
import { useChat } from '@/app/chat/hooks/use-chat'
import { ChatHeader } from './chat-header'
import { ChatInput } from './chat-input'
import { MessageList } from './message-list'
import { ChatScrollAnchor } from './chat-scroll-anchor'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { NewChatDialog } from './new-chat-dialog'
import { DeleteChatDialog } from './delete-chat-dialog'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { matrixStyles } from '@/components/ui/matrix-styles'

interface ChatUIProps {
  className?: string
}

export function ChatUI({ className }: ChatUIProps) {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    startNewChat,
    sessions,
    currentSession,
    selectChat,
    deleteChat,
    progress,
    isAiThinking,
  } = useChat()

  const [isNewChatOpen, setIsNewChatOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)

  const handleNewChat = () => {
    setIsNewChatOpen(true)
  }

  const handleCreateChat = async (title: string) => {
    await startNewChat(title)
    setIsNewChatOpen(false)
  }

  const handleDeleteChat = async () => {
    await deleteChat()
    setIsDeleteDialogOpen(false)
  }

  return (
    <div className={cn(
      matrixStyles.layout.base,
      'fixed left-1/2 -translate-x-1/2 top-12',
      'w-full max-w-7xl',
      'h-[calc(100vh-theme(spacing.20)-theme(spacing.8))] overflow-hidden'
    )}>
      <div className={matrixStyles.layout.gradient} />
      <Card className={cn(
        'flex h-full flex-col mb-8',
        'bottom-4',
        'border-0 rounded-none',
        matrixStyles.card.base,
        matrixStyles.card.shadow,
        className
      )}>
        <ChatHeader 
          isLoading={isLoading} 
          onNewChat={handleNewChat}
          onSelectChat={selectChat}
          onClearChat={() => setIsDeleteDialogOpen(true)}
          sessions={sessions}
          currentSession={currentSession}
          progress={progress}
        />
        
        <ScrollArea className="flex-1 px-4">
          <MessageList
            messages={messages}
            isLoading={isLoading}
            isAiThinking={isAiThinking}
            isEmpty={messages.length === 0}
          />
          <ChatScrollAnchor trackVisibility={true} />
        </ScrollArea>

        <div className="border-t bg-background/50 p-4">
          <ChatInput
            input={input}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            lastMessageId={messages[messages.length - 1]?.id}
            hasActiveSession={!!currentSession}
          />
          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <NewChatDialog
          isOpen={isNewChatOpen}
          onClose={() => setIsNewChatOpen(false)}
          onCreateChat={handleCreateChat}
        />
        <DeleteChatDialog 
          isOpen={isDeleteDialogOpen}
          onClose={() => setIsDeleteDialogOpen(false)}
          onConfirm={handleDeleteChat}
          currentSession={currentSession}
        />
      </Card>
    </div>
  )
} 