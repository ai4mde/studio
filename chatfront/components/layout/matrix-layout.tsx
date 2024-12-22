'use client'

import { cn } from "@/lib/utils"
import { useTheme } from "next-themes"

interface MatrixLayoutProps {
  children: React.ReactNode
  className?: string
}

export function MatrixLayout({ children, className }: MatrixLayoutProps) {
  const { theme } = useTheme()

  return (
    <div className={cn(
      'min-h-screen',
      'bg-background text-foreground',
      'transition-colors duration-300',
      className
    )}>
      <div className={cn(
        'fixed inset-0 -z-10',
        'bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(var(--primary),0.15),rgba(255,255,255,0))]',
        'dark:bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(var(--primary),0.3),rgba(0,0,0,0))]'
      )} />
      {children}
    </div>
  )
} 