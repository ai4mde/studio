'use client'

import { cn } from "@/lib/utils"

interface MatrixLayoutProps {
  children: React.ReactNode
  className?: string
}

export function MatrixLayout({ children, className }: MatrixLayoutProps) {
  return (
    <div className={cn(
      'min-h-screen',
      'bg-background text-foreground',
      'transition-colors duration-300 ease-in-out',
      'relative',
      className
    )}>
      <div className={cn(
        'fixed inset-0 -z-10',
        'pointer-events-none',
        'bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,hsl(var(--primary)/0.15),transparent)]',
        'dark:bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,hsl(var(--primary)/0.3),transparent)]',
        'transition-opacity duration-300'
      )} />
      {children}
    </div>
  )
} 