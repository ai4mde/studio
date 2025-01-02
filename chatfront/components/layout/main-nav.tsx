import Link from "next/link"
import { cn } from "@/lib/utils"

export function MainNav() {
  return (
    <div className="flex gap-6 md:gap-10">
      <Link 
        href="/" 
        className={cn(
          "flex items-center space-x-2",
          "text-foreground hover:text-primary",
          "transition-colors duration-200"
        )}
      >
        <span className="font-bold tracking-tight">AI4MDE</span>
      </Link>
    </div>
  )
} 