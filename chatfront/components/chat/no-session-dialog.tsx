'use client'

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogFooter,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog"
import { MessageCircleOff } from "lucide-react"

interface NoSessionDialogProps {
  isOpen: boolean
  onClose: () => void
}

export function NoSessionDialog({ isOpen, onClose }: NoSessionDialogProps) {
  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-[360px]">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <MessageCircleOff className="h-5 w-5" />
            No Active Chat
          </AlertDialogTitle>
          <AlertDialogDescription>
            Please start a new chat or select an existing one to continue.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onClose}>
            Close
          </AlertDialogCancel>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
} 