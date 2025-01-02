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
      <DialogContent className="bg-background border-border">
        <DialogHeader>
          <DialogTitle className="text-foreground">Start New Chat</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Would you like to start a new chat or reset the current one?
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-2">
          <Button 
            variant="outline" 
            onClick={onReset}
            className="bg-background hover:bg-muted"
          >
            Reset Current
          </Button>
          <Button 
            onClick={onNewChat}
            className="bg-primary text-primary-foreground hover:bg-primary/90"
          >
            New Chat
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
} 