'use client'

import { useState } from 'react'
import { Loader2, Menu, Plus, Trash2, MousePointerClick } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { ChatSession } from "@/app/chat/types"
import { DeleteChatDialog } from "./delete-chat-dialog"
import { ProgressBar } from './progress-bar'

interface ChatHeaderProps {
  isLoading?: boolean
  onNewChat: () => void
  onSelectChat: (sessionId: string) => void
  onClearChat?: () => void
  sessions: ChatSession[]
  currentSession: ChatSession | null
  progress?: number
}

export function ChatHeader({ 
  isLoading, 
  onNewChat, 
  onSelectChat, 
  onClearChat, 
  sessions = [], 
  currentSession, 
  progress 
}: ChatHeaderProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)

  return (
    <header className="sticky top-0 z-10 bg-background border-b border-border">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-2">
          {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          <span className="font-bold text-foreground">
            {currentSession?.title || 'New Chat'}
          </span>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 text-foreground">
              <Menu className="h-4 w-4" />
              <span>Chat Menu</span>
              <span className="sr-only">Open menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-popover border-border">
            <DropdownMenuItem onClick={onNewChat} className="text-foreground">
              <Plus className="mr-2 h-4 w-4" />
              New Chat
            </DropdownMenuItem>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="text-foreground">
                <MousePointerClick className="mr-2 h-4 w-4" />
                Select Chat ({sessions?.length || 0})
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="bg-popover border-border">
                {sessions && sessions.length > 0 ? (
                  sessions.map((session) => (
                    <DropdownMenuItem
                      key={session.id}
                      onClick={() => onSelectChat(session.id)}
                      className="text-foreground"
                    >
                      {session.title}
                    </DropdownMenuItem>
                  ))
                ) : (
                  <DropdownMenuItem disabled className="text-muted-foreground">
                    No chats available
                  </DropdownMenuItem>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuItem 
              onClick={() => setIsDeleteDialogOpen(true)} 
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Chat
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {progress !== undefined && (
        <div className="px-4 pb-2">
          <ProgressBar 
            progress={progress} 
            showPercentage={true}
          />
        </div>
      )}

      <DeleteChatDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={async () => {
          if (onClearChat) await onClearChat();
        }}
        currentSession={currentSession}
      />
    </header>
  )
} 