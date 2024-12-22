'use client'

import { usePathname } from "next/navigation"
import { Footer } from "@/components/layout/footer"

export function FooterWrapper() {
  const pathname = usePathname()
  const isChat = pathname === '/chat'

  if (isChat) return null

  return <Footer />
} 