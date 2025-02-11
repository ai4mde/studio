import * as React from "react"
import { cn } from "../../lib/utils"

interface ThemeColorsProps {
  className?: string
}

export function ThemeColors({ className }: ThemeColorsProps) {
  return (
    <div className={cn("grid gap-4", className)}>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Primary</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-primary" />
          <div className="h-10 rounded-md bg-primary-foreground" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Secondary</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-secondary" />
          <div className="h-10 rounded-md bg-secondary-foreground" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Accent</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-accent" />
          <div className="h-10 rounded-md bg-accent-foreground" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Destructive</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-destructive" />
          <div className="h-10 rounded-md bg-destructive-foreground" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Card</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-card" />
          <div className="h-10 rounded-md bg-card-foreground" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Muted</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-muted" />
          <div className="h-10 rounded-md bg-muted-foreground" />
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Background</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="h-10 rounded-md bg-background" />
          <div className="h-10 rounded-md bg-foreground" />
        </div>
      </div>
    </div>
  )
} 