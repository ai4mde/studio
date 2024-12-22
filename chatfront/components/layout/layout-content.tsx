'use client'

import { usePathname } from 'next/navigation'
import NavBar from '@/components/navigation/navbar'
import { Footer } from '@/components/layout/footer'
import { InactivityProvider } from '@/components/providers/inactivity-provider'
import { cn } from '@/lib/utils'

// Define paths that require inactivity monitoring
const PROTECTED_PATHS = ['/chat', '/srsdocs'] as const

interface LayoutContentProps {
  children: React.ReactNode
}

export function LayoutContent({ children }: LayoutContentProps) {
  const pathname = usePathname()
  const requiresInactivityCheck = PROTECTED_PATHS.some(path => pathname?.startsWith(path))

  return (
    <>
      {requiresInactivityCheck ? (
        <InactivityProvider>
          <div className={cn(
            'relative min-h-screen flex flex-col',
            'bg-background text-foreground'
          )}>
            <NavBar />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </InactivityProvider>
      ) : (
        <div className={cn(
          'relative min-h-screen flex flex-col',
          'bg-background text-foreground'
        )}>
          <NavBar />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      )}
    </>
  )
} 