import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function hslToHex(hslVar: string): string {
  // Get the CSS variable value
  const hsl = getComputedStyle(document.documentElement)
    .getPropertyValue(hslVar)
    .trim()
  
  // Parse HSL values
  const [h, s, l] = hsl.split(' ').map(Number)
  
  // Convert to RGB
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs((h / 60) % 2 - 1))
  const m = l - c/2
  let r = 0, g = 0, b = 0
  
  if (0 <= h && h < 60) {
    [r, g, b] = [c, x, 0]
  } else if (60 <= h && h < 120) {
    [r, g, b] = [x, c, 0]
  } else if (120 <= h && h < 180) {
    [r, g, b] = [0, c, x]
  } else if (180 <= h && h < 240) {
    [r, g, b] = [0, x, c]
  } else if (240 <= h && h < 300) {
    [r, g, b] = [x, 0, c]
  } else if (300 <= h && h < 360) {
    [r, g, b] = [c, 0, x]
  }
  
  // Convert to hex
  const toHex = (n: number) => {
    const hex = Math.round((n + m) * 255).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}
