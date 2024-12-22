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
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5" />
            Delete Chat
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to delete &quot;{currentSession?.title || 'this chat'}&quot;? 
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button 
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
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