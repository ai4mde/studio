'use client'

import { useRef, KeyboardEvent, useEffect, useCallback } from 'react'
import TextareaAutosize from 'react-textarea-autosize'
import { Button } from '@/components/ui/button'
import { SendHorizontal, MessageCircleOff } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
  handleSubmit: (e: React.FormEvent) => void
  isLoading?: boolean
  lastMessageId?: string
  hasActiveSession: boolean
}

export function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  lastMessageId,
  hasActiveSession
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Focus management function
  const focusInput = useCallback(() => {
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [])

  // Initial focus and window focus handling
  useEffect(() => {
    if (hasActiveSession) {
      focusInput()
      window.addEventListener('focus', focusInput)

      return () => {
        window.removeEventListener('focus', focusInput)
      }
    }
  }, [focusInput, hasActiveSession])

  // Re-focus when new message arrives
  useEffect(() => {
    if (lastMessageId && !isLoading && hasActiveSession) {
      requestAnimationFrame(focusInput)
    }
  }, [lastMessageId, isLoading, focusInput, hasActiveSession])

  // Re-focus after submitting
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      handleSubmit(e)
      // Use requestAnimationFrame for smoother focus handling
      requestAnimationFrame(focusInput)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim()) {
        handleFormSubmit(e)
      }
    }
  }

  if (!hasActiveSession) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <MessageCircleOff className="h-8 w-8 mb-4 text-muted-foreground" />
        <p className="text-lg font-semibold text-foreground">
          No Active Chat
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Please start a new chat or select an existing one to continue.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleFormSubmit}>
      <div className={cn(
        "relative flex items-center",
        "p-4",
        "bottom-4",
        "max-w-7xl mx-auto w-full",
        "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      )}>
        <div className="relative w-full h-auto">
          <TextareaAutosize
            ref={textareaRef}
            tabIndex={0}
            minRows={4}
            maxRows={12}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Press Shift+Enter for new line)"
            spellCheck={false}
            className={cn(
              "min-h-[48px] w-full resize-none pr-10",
              "bg-background px-4 py-3",
              "rounded-md border border-border",
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
  )
} 