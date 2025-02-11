import * as React from 'react';
import { useState } from 'react';
import { Loader2, Menu, Plus, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "../ui/dropdown-menu";
import { Button } from "../ui/button";
import type { ChatSession } from "../../types/chat.types";
import { DeleteChatDialog } from "./delete-chat-dialog";
import { Progress } from "../ui/progress";

interface ChatHeaderProps {
  isLoading?: boolean;
  onNewChat: () => void;
  onSelectChat: (sessionId: number) => void;
  onClearChat?: () => void;
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  progress?: number;
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
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const handleDeleteClick = () => {
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      if (onClearChat) {
        await onClearChat();
      }
      setIsDeleteDialogOpen(false);
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  return (
    <header className="sticky top-0 z-10 bg-background border-b">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-2">
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          <span className="font-bold text-foreground">
            {currentSession?.title || 'New Chat'}
          </span>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2">
              <Menu className="h-4 w-4" />
              <span>Chat Menu</span>
              <span className="sr-only">Open menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onNewChat}>
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </DropdownMenuItem>
            {sessions.length > 0 && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Menu className="h-4 w-4 mr-2" />
                  Select Chat
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  {sessions.map((session) => (
                    <DropdownMenuItem
                      key={session.id}
                      onClick={() => onSelectChat(session.id)}
                    >
                      {session.title}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )}
            {currentSession && (
              <DropdownMenuItem 
                onClick={handleDeleteClick}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Chat
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {progress !== undefined && (
        <div className="px-4 pb-2">
          <div className="flex items-center gap-2">
            <div className="flex-1">
              <Progress value={progress} className="h-2" />
            </div>
            <span className="text-sm text-muted-foreground w-12 text-right">
              {Math.round(progress)}%
            </span>
          </div>
        </div>
      )}

      <DeleteChatDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        currentSession={currentSession}
      />
    </header>
  );
} 