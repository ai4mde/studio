import * as React from 'react';
import { useState, useRef, useEffect } from 'react';
import { json, redirect } from '@remix-run/node';
import type { LoaderFunction, ActionFunction } from '@remix-run/node';
import { useChat } from '../hooks/use-chat';
import { ChatHeader } from '../components/chat/chat-header';
import { ChatInput } from '../components/chat/chat-input';
import { ChatMessage } from '../components/chat/chat-message';
import { NewChatDialog } from '../components/chat/new-chat-dialog';
import { Alert, AlertDescription } from '../components/ui/alert';
import { requireUser } from '../services/session.server';
import { ScrollArea } from '../components/ui/scroll-area';
import { Card } from '../components/ui/card';
import { cn } from '../lib/utils';
import { SessionTimeoutWarning } from '../components/layout/session-timeout-warning';
import { useNavigate, useLoaderData, Form } from '@remix-run/react';
import { logout } from '../services/session.server';

export const loader: LoaderFunction = async ({ request }) => {
  try {
    await requireUser(request);
    return json({
      sessionTimeoutMinutes: Number(process.env.SESSION_TIMEOUT_MINUTES) || 30
    });
  } catch (error) {
    return redirect('/login?redirectTo=/chat');
  }
};

export const action: ActionFunction = async ({ request }) => {
  if (request.method === "POST") {
    return logout(request);
  }
  return null;
};

export default function Chat() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    startNewChat,
    sessions,
    currentSession,
    selectChat,
    deleteChat,
    progress,
  } = useChat();
  
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const isAutoScrollEnabled = useRef(true);
  const lastMessageRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { sessionTimeoutMinutes } = useLoaderData<typeof loader>();

  // Auto scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current && isAutoScrollEnabled.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isLoading]);

  // Handle scroll events to determine auto-scroll behavior
  useEffect(() => {
    const scrollContainer = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]');
    if (!scrollContainer) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
      const isNearBottom = scrollHeight - (scrollTop + clientHeight) < 100;
      isAutoScrollEnabled.current = isNearBottom;
    };

    scrollContainer.addEventListener('scroll', handleScroll);
    return () => scrollContainer.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNewChat = async (title: string) => {
    await startNewChat(title);
    setIsNewChatOpen(false);
  };

  const handleTimeout = () => {
    (document.getElementById('logoutForm') as HTMLFormElement)?.submit();
  };

  return (
    <div className="container py-8 mx-auto">
      <Card className="h-[calc(100vh-16rem)] flex flex-col border-0">
        <ChatHeader 
          isLoading={isLoading}
          onNewChat={() => setIsNewChatOpen(true)}
          onSelectChat={selectChat}
          onClearChat={deleteChat}
          sessions={sessions}
          currentSession={currentSession}
          progress={progress}
        />
        <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
          {messages.map((message, index) => (
            <div
              key={index}
              ref={index === messages.length - 1 ? lastMessageRef : null}
            >
              <ChatMessage
                message={message}
                isLoading={isLoading && index === messages.length - 1}
              />
            </div>
          ))}
          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </ScrollArea>
        <div className="p-4 border-t">
          <ChatInput
            input={input}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            hasActiveSession={!!currentSession}
          />
        </div>
      </Card>
      <NewChatDialog
        isOpen={isNewChatOpen}
        onClose={() => setIsNewChatOpen(false)}
        onCreateChat={handleNewChat}
      />
      <Form method="post" id="logoutForm" className="hidden" />
      <SessionTimeoutWarning 
        timeoutMinutes={sessionTimeoutMinutes}
        onTimeout={handleTimeout}
      />
    </div>
  );
} 