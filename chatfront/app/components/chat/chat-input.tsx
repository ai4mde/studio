import * as React from 'react';
import { useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { SendHorizontal, MessageCircleOff } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Textarea } from '../ui/textarea';

interface ChatInputProps {
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  isLoading?: boolean;
  lastMessageId?: string;
  hasActiveSession: boolean;
}

export function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  lastMessageId,
  hasActiveSession
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  useEffect(() => {
    if (!isLoading && textareaRef.current && hasActiveSession) {
      textareaRef.current.focus();
    }
  }, [isLoading, hasActiveSession]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(e);
  };

  if (!hasActiveSession) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <MessageCircleOff className="h-8 w-8 mb-4 text-muted-foreground" />
        <p className="text-lg font-semibold">
          No Active Chat
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Please start a new chat or select an existing one to continue.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleFormSubmit}>
      <div className={cn(
        "relative flex items-center",
        "px-8 py-4",
        "max-w-7xl mx-auto w-full",
        "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      )}>
        <div className="relative w-full">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            className={cn(
              "min-h-[80px] w-full resize-none pr-12",
              "bg-background",
              "rounded-md border border-input",
              "focus-visible:outline-none focus-visible:ring-1",
              "focus-visible:ring-ring",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "text-foreground placeholder:text-muted-foreground",
              "scrollbar-custom"
            )}
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            disabled={isLoading || !input.trim()}
            className={cn(
              "absolute right-2 bottom-2",
              "bg-primary text-primary-foreground",
              "hover:bg-primary/90",
              "focus-visible:ring-1 focus-visible:ring-ring",
              "disabled:opacity-50"
            )}
          >
            <SendHorizontal className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
      </div>
    </form>
  );
} 