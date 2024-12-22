'use client'

import Image from 'next/image'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import Logo from '@/app/assets/logo.svg'

interface EmptyScreenProps {
  className?: string
}

export function EmptyScreen({ className }: EmptyScreenProps) {
  return (
    <div className="flex-1 flex items-center justify-center min-h-[calc(60vh)]">
      <Card className={cn(
        'flex flex-col items-center justify-center',
        'p-8 space-y-6',
        'bg-background/60 backdrop-blur',
        'max-w-md mx-auto',
        className
      )}>
        <Image 
          src={Logo}
          alt="AI4MDE Logo"
          width={96}
          height={96}
          priority
        />
        <div className="text-center space-y-2">
          <h2 className="text-xl font-semibold text-foreground">
            Welcome to AI4MDE Chat
          </h2>
          
        </div>
      </Card>
    </div>
  )
} 