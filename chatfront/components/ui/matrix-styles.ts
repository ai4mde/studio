// Matrix-specific utility styles
export const matrixStyles = {
  card: {
    base: "bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60",
    shadow: "shadow-lg dark:shadow-primary/10",
    border: "border-border/50",
    hover: "transition-all duration-300 hover:shadow-primary/5",
  },
  layout: {
    base: [
      "min-h-screen",
      "bg-background text-foreground",
      "transition-colors duration-300"
    ].join(" "),
    gradient: [
      "fixed inset-0 -z-10",
      "bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(var(--primary),0.15),rgba(255,255,255,0))]",
      "dark:bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(var(--primary),0.3),rgba(0,0,0,0))]"
    ].join(" ")
  },
  // Additional Matrix-themed styles
  text: {
    glow: "text-primary drop-shadow-[0_0_10px_rgba(var(--primary),0.3)]",
    fade: "transition-opacity duration-300",
  },
  effects: {
    scanline: "before:content-[''] before:absolute before:inset-0 before:bg-scanline before:animate-scanline before:pointer-events-none",
    flicker: "animate-flicker",
    pulse: "animate-pulse",
  }
} as const
