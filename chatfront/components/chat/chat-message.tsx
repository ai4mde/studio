'use client'

import { Message } from '@/app/chat/types'
import { Markdown } from '@/components/markdown'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card } from "@/components/ui/card"
import AILogo from '@/app/assets/logo.svg'
import UserAvatar from '@/app/assets/user-avatar.svg'
import { matrixStyles } from "@/components/ui/matrix-styles"

interface ChatMessageProps {
  message: Message
  isLoading?: boolean
  className?: string
}

export function ChatMessage({ message, isLoading, className }: ChatMessageProps) {
  const isUser = message.role === 'USER'

  return (
    <div className={cn('flex gap-4 p-4', isUser && 'flex-row-reverse', className)}>
      <Avatar className="h-12 w-12 shrink-0">
        <AvatarImage 
          src={isUser ? UserAvatar.src : AILogo.src} 
          alt={isUser ? 'User' : 'Agent Smith'}
          className="object-contain p-2"
        />
        <AvatarFallback className="bg-muted text-muted-foreground">
          {isUser ? 'U' : 'A'}
        </AvatarFallback>
      </Avatar>

      <Card className={cn(
        'flex-1 p-4',
        isUser 
          ? 'bg-primary/15 border-primary/30 text-foreground dark:bg-primary/20' 
          : 'bg-muted/90 border-muted-foreground/20 text-foreground dark:bg-secondary/30',
        'border shadow-sm',
        matrixStyles.card.base,
        matrixStyles.card.shadow
      )}>
        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground animate-pulse">
            <span>Agent Smith is thinking</span>
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
        ) : (
          <div className={cn(
            'prose dark:prose-invert max-w-none',
            'prose-p:leading-relaxed prose-pre:p-0',
            'prose-code:bg-muted/30 prose-code:text-foreground',
            'prose-headings:text-foreground prose-a:text-primary',
            'prose-strong:text-foreground',
            'prose-ul:text-foreground prose-ol:text-foreground',
            'prose-blockquote:text-foreground prose-blockquote:border-l-primary'
          )}>
            <Markdown content={message.content} />
          </div>
        )}
      </Card>
    </div>
  )
} 