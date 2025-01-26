import { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { auth } from "@/auth"
import { ChatUI } from "@/components/chat/chat-ui"

export const metadata: Metadata = {
  title: 'Chat | AI4MDE',
  description: 'Chat with AI4MDE assistant',
}

export default async function ChatPage() {
  const session = await auth()
  
  if (!session?.user) {
    redirect('/login')
  }

  return (
    <main className="flex flex-col min-h-screen bg-background">
      <div className="container mx-auto">
        <ChatUI />
      </div>
    </main>
  )
}

