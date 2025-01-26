'use client'

import { useState } from 'react'
import { useChat } from '@/app/chat/hooks/use-chat'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
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
  const { status } = useSession()
  
  if (status === 'unauthenticated') {
    redirect('/login')
  }

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

  const handleNewChat = async (title: string) => {
    await startNewChat(title);
  };

  return (
    <div className={cn(
      matrixStyles.layout.base,
      'fixed left-1/2 -translate-x-1/2 top-12',
      'w-full max-w-7xl',
      'h-[calc(100vh-theme(spacing.20)-theme(spacing.8))] overflow-hidden',
      className
    )}>
      <div className={matrixStyles.layout.gradient} />
      <Card className={cn(
        'flex h-full flex-col mb-8',
        'border-0 rounded-none',
        'bg-background/95 backdrop-blur',
        'supports-[backdrop-filter]:bg-background/60',
        matrixStyles.card.base,
        matrixStyles.card.shadow
      )}>
        <ChatHeader 
          isLoading={isLoading} 
          onNewChat={() => setIsNewChatOpen(true)}
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

        <div className="border-t border-border">
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
          onCreateChat={handleNewChat}
        />
        <DeleteChatDialog 
          isOpen={isDeleteDialogOpen}
          onClose={() => setIsDeleteDialogOpen(false)}
          onConfirm={async () => {
            if (currentSession) {
              await deleteChat(currentSession.id)
            }
          }}
          currentSession={currentSession}
        />
      </Card>
    </div>
  )
} 