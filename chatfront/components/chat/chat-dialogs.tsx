'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface ChatDialogsProps {
  isOpen: boolean
  onClose: () => void
  onReset: () => void
  onNewChat: () => void
}

export function ChatDialogs({ isOpen, onClose, onReset, onNewChat }: ChatDialogsProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Start New Chat</DialogTitle>
          <DialogDescription>
            Would you like to start a new chat or reset the current one?
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onReset}>
            Reset Current
          </Button>
          <Button onClick={onNewChat}>
            New Chat
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
} 