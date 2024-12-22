import { ChatRole } from '../types/chat';

export async function sendChatMessage(message: string) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      role: ChatRole.USER,
      content: message
    })
  });
  return response;
} 