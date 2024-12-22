'use client'

import NavBar from "@/components/navigation/navbar"

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <NavBar />
      </div>
    </header>
  )
} 