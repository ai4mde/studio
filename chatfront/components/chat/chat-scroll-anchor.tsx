'use client'

import { useInView } from 'react-intersection-observer'
import { useEffect } from 'react'
import { cn } from '@/lib/utils'

interface ChatScrollAnchorProps {
  trackVisibility?: boolean
  className?: string
  scrollBehavior?: ScrollBehavior
  scrollMargin?: string
}

export function ChatScrollAnchor({ 
  trackVisibility,
  className,
  scrollBehavior = 'smooth',
  scrollMargin = '0px 0px -150px 0px'
}: ChatScrollAnchorProps) {
  const { ref, entry } = useInView({
    trackVisibility,
    delay: 100,
    rootMargin: scrollMargin
  })

  useEffect(() => {
    if (entry?.isIntersecting) {
      entry.target.scrollIntoView({
        block: 'start',
        behavior: scrollBehavior
      })
    }
  }, [entry, scrollBehavior])

  return (
    <div 
      ref={ref} 
      className={cn(
        'h-[1px] w-full',
        'opacity-0 pointer-events-none',
        className
      )} 
      aria-hidden="true"
    />
  )
} 