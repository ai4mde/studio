# Visual Theme & Atmosphere
Linear - Project management for engineers. Ultra-minimal, precise, dark theme with a purple accent. 
Void-black canvas, subtle borders, and high-contrast typography.

## Color Palette & Roles
| Role | Hex | Description |
|---|---|---|
| Primary | #6366f1 | Indigo accent for buttons and active states |
| Background | #000000 | Pure black for the main canvas |
| Surface | #0a0a0a | Slightly lighter black for cards and sections |
| Border | #1f1f1f | Subtle dark gray for dividers and borders |
| Text Base | #ffffff | Crisp white for headings |
| Text Muted | #a1a1aa | Gray for secondary text |

## Typography Rules
Font Family: Inter, sans-serif
- H1: 2.5rem, weight 600, tracking -0.02em
- Body: 1rem, weight 400, leading 1.6
- Mono: JetBrains Mono, 0.875rem

## Component Stylings
### Buttons
- Radius: 6px
- Primary: bg-[#6366f1] text-white hover:opacity-90 transition-all
- Outline: border border-[#1f1f1f] bg-transparent text-white hover:bg-[#1f1f1f]
- Shadow: 0 4px 12px rgba(99, 102, 241, 0.2)

### Cards
- Radius: 8px
- Border: 1px solid #1f1f1f
- Background: #0a0a0a
- Hover: border-[#6366f1] transition-colors

### Inputs
- Background: #0a0a0a
- Border: 1px solid #1f1f1f
- Focus: border-[#6366f1] ring-1 ring-[#6366f1]

## Agent Prompt Guide
When generating UI for this project, always use `bg-[#000000]` for the body and `bg-[#0a0a0a]` for containers. 
Use `border-[#1f1f1f]` for all separations. 
Accents should strictly be `indigo-500` (#6366f1).
Keep spacing tight and typography high-contrast.
