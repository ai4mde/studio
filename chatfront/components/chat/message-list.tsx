'use client'

import { useEffect, useRef } from 'react'
import { Message } from '@/app/chat/types'
import { ChatMessage } from './chat-message'
import { EmptyScreen } from './empty-screen'
import { cn } from '@/lib/utils'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  isAiThinking: boolean
  isEmpty: boolean
  className?: string
}

export function MessageList({ 
  messages, 
  isLoading, 
  isAiThinking,
  isEmpty,
  className 
}: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  if (isEmpty) {
    return <EmptyScreen />
  }

  return (
    <div 
      ref={scrollRef} 
      className={cn(
        'flex-1 overflow-y-auto px-4',
        'space-y-4',
        className
      )}
    >
      {messages.map((message, index) => {
        const isLastMessage = index === messages.length - 1
        
        return (
          <ChatMessage
            key={message.id}
            message={message}
            isLoading={isLoading && isLastMessage}
          />
        )
      })}
      {(isLoading || isAiThinking) && (
        <ChatMessage
          message={{
            role: 'ASSISTANT',
            content: '',
            id: 'thinking',
            created_at: new Date().toISOString()
          }}
          isLoading={true}
        />
      )}
      <div ref={messagesEndRef} />
    </div>
  )
} 