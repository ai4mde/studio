'use client'

import { cn } from '@/lib/utils'

interface ProgressBarProps {
  progress: number
  showPercentage?: boolean
  className?: string
}

export function ProgressBar({ 
  progress, 
  showPercentage = false,
  className 
}: ProgressBarProps) {
  const percentage = Math.round(progress)

  return (
    <div className={cn('flex items-center gap-2 w-full', className)}>
      <div className="flex-1 h-2.5 bg-muted rounded-full overflow-hidden">
        <div 
          className={cn(
            'h-full bg-primary',
            'transition-all duration-500 ease-out',
            'rounded-full'
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span className="sr-only">{percentage}% Complete</span>
        </div>
      </div>
      {showPercentage && (
        <span className="text-sm text-muted-foreground shrink-0">
          {percentage}%
        </span>
      )}
    </div>
  )
} 