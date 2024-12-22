import { ChatUI } from "@/components/chat/chat-ui"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: 'Chat | AI4MDE',
  description: 'Chat with AI4MDE assistant',
}

export default async function ChatPage() {
  return (
    <div className="container mx-auto">
      {/* <h1 className="text-2xl font-bold mb-4">Chat with AI4MDE</h1> */}
      <ChatUI />
    </div>
  )
}

