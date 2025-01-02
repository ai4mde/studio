'use client';

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ChatSession } from "@/app/chat/types"
import { Trash2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface DeleteChatDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
  currentSession: ChatSession | null
}

export function DeleteChatDialog({
  isOpen,
  onClose,
  onConfirm,
  currentSession
}: DeleteChatDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (isDeleting) return
    
    try {
      setIsDeleting(true)
      await onConfirm()
      onClose()
    } catch (error) {
      console.error('Failed to delete chat:', error)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-background border-border">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-foreground">
            <Trash2 className="h-5 w-5 text-destructive" />
            Delete Chat
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Are you sure you want to delete &quot;{currentSession?.title || 'this chat'}&quot;? 
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={onClose}
            disabled={isDeleting}
            className="bg-background hover:bg-muted"
          >
            Cancel
          </Button>
          <Button 
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 