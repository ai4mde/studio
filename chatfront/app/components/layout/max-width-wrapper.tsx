import * as React from "react"
import { cn } from "../../lib/utils"

interface MaxWidthWrapperProps extends React.HTMLAttributes<HTMLDivElement> {}

export default function MaxWidthWrapper({
  className,
  ...props
}: MaxWidthWrapperProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-screen-xl px-2.5 md:px-20",
        className
      )}
      {...props}
    />
  )
} 