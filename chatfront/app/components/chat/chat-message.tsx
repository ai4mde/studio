import * as React from 'react';
import type { Message } from '../../types/chat.types';
import { Markdown } from '../layout/markdown';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Card } from "../ui/card";

interface ChatMessageProps {
  message: Message;
  isLoading?: boolean;
  className?: string;
}

export function ChatMessage({ message, isLoading, className }: ChatMessageProps) {
  const isUser = message.role === 'USER';

  return (
    <div className={cn('flex gap-4 p-4', isUser && 'flex-row-reverse', className)}>
      <Avatar className={cn(
        "h-8 w-8 shrink-0",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
      )}>
        <AvatarFallback>{isUser ? 'U' : 'A'}</AvatarFallback>
      </Avatar>

      <Card className={cn(
        'flex-1 p-4',
        isUser ? 'bg-primary/5' : 'bg-background',
        'border shadow-sm'
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
            'prose-code:bg-muted prose-code:text-foreground',
            'prose-headings:text-foreground prose-a:text-primary'
          )}>
            <Markdown content={message.content} />
          </div>
        )}
      </Card>
    </div>
  );
} 