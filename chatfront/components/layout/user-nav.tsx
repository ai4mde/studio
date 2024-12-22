'use client'

import { useSession, signIn, signOut } from "next-auth/react"
import { Button } from "@/components/ui/button"

export function UserNav() {
  const { data: session } = useSession()

  if (!session) {
    return (
      <Button variant="ghost" onClick={() => signIn()}>
        Sign In
      </Button>
    )
  }

  return (
    <Button variant="ghost" onClick={() => signOut()}>
      Sign Out
    </Button>
  )
} 