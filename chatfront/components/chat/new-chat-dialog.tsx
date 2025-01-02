'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, MessageSquarePlus } from "lucide-react"

interface NewChatDialogProps {
  isOpen: boolean
  onClose: () => void
  onCreateChat: (title: string) => Promise<void>
}

export function NewChatDialog({
  isOpen,
  onClose,
  onCreateChat
}: NewChatDialogProps) {
  const [title, setTitle] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const handleCreate = async () => {
    if (!title.trim() || isCreating) return

    try {
      setIsCreating(true)
      await onCreateChat(title)
      setTitle('')
      onClose()
    } catch (error) {
      console.error('Failed to create chat:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleCreate()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-background border-border">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-foreground">
            <MessageSquarePlus className="h-5 w-5 text-primary" />
            New Chat
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Create a new chat session. Give it a descriptive title.
          </DialogDescription>
        </DialogHeader>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter chat title..."
          disabled={isCreating}
          autoFocus
          className="bg-background border-border"
        />
        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={onClose}
            disabled={isCreating}
            className="bg-background hover:bg-muted"
          >
            Cancel
          </Button>
          <Button 
            onClick={handleCreate}
            disabled={!title.trim() || isCreating}
            className="bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {isCreating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 