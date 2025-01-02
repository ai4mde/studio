'use client'

import { useSession, signIn, signOut } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { LogIn, LogOut } from "lucide-react"

export function UserNav() {
  const { data: session } = useSession()

  if (!session) {
    return (
      <Button 
        variant="ghost" 
        onClick={() => signIn()}
        className="text-foreground hover:text-primary hover:bg-muted"
      >
        <LogIn className="h-4 w-4 mr-2" />
        Sign In
      </Button>
    )
  }

  return (
    <Button 
      variant="ghost" 
      onClick={() => signOut()}
      className="text-foreground hover:text-primary hover:bg-muted"
    >
      <LogOut className="h-4 w-4 mr-2" />
      Sign Out
    </Button>
  )
} 