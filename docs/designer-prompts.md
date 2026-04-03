# Designer Prompt Examples

This document provides example prompts for the human-in-the-loop UI generation workflow.

---

## Generate Candidates (`/generate_candidates/`)

The initial generation prompt. Describe the visual style and layout you want.

### Minimal / Clean
```
A clean, minimal interface with lots of white space. Use a sidebar layout with a light gray background and indigo accent color. Rounded corners.
```

### Dark Dashboard
```
A dark analytics dashboard layout. Dark navy background, bright teal accent, monospaced font. Icon-only sidebar with tooltips.
```

### Corporate / Professional
```
A professional corporate interface with a top navigation bar. White background, deep blue accent. No rounded corners, flat buttons.
```

### Mobile-Friendly / Card-Based
```
A card-based layout using a top navigation. Soft shadow cards, rounded corners (radius 16), pastel green accent. Use the Inter font from Google Fonts.
```

### Abstract / Artistic
```
An abstract, bold interface. Large typography, high-contrast colors, black background with bright yellow accent. Minimal navigation using a sidebar.
```

---

## Refine Interface (`/refine/`)

After selecting a candidate, use these prompts to iteratively adjust specific aspects.

### Change Font
```
Change the font to Roboto. Use https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap
```

```
Use a serif font — Merriweather from Google Fonts. Keep everything else the same.
```

### Change Colors
```
Change the accent color to #E11D48 (rose red). Keep the layout and font.
```

```
Switch to a dark theme. Background #0F172A, text white, accent #38BDF8.
```

### Change Layout
```
Switch the navigation from sidebar to top navigation bar.
```

```
Change to a minimal layout — hide the sidebar, use a floating top bar only.
```

### Add Custom CSS Effects
```
Add a glassmorphism effect to all cards: semi-transparent white background with blur. Make the sidebar also slightly transparent.
```

```
Add a subtle gradient to the top navigation bar from the accent color to a darker shade. Add a bottom border to table rows only, no side borders.
```

```
Make buttons have a pill shape (border-radius 999px). Add a hover scale animation (transform scale 1.02) to all cards.
```

### Typography
```
Increase base font size to 15px. Make table headers bold and uppercase. Use a slightly larger heading size.
```

```
Use the Poppins font from Google Fonts. Increase line height to 1.7 for better readability.
```

### Layout Adjustments
```
Make the sidebar wider (224px instead of the default). Move the logout button to the bottom of the sidebar.
```

```
Add a sticky page header. The title and action buttons should stay visible when scrolling.
```

### Accessibility
```
Increase color contrast on all text. Use a minimum font size of 14px everywhere. Make focus outlines more visible.
```

---

## Combined / Advanced Prompts

### Full Redesign (uses all styling fields)
```
Redesign with a dark sidebar (#1E1E2E), white main area, purple accent (#7C3AED). Use the Inter font from https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap. Add card shadows and pill-shaped buttons.
```

### Brand-Specific
```
Apply a brand style: primary color #0EA5E9, background #F0F9FF, font Nunito from Google Fonts (https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap). All cards have a 1px solid #BAE6FD border and no shadow.
```

### Material Design Inspired
```
Apply Material Design 3 style: use Roboto font, background #FFFBFE, accent #6750A4, surface cards with 2px elevation shadow, rounded corners 12px. Add ripple effect placeholder classes on buttons.
```

---

## Notes

- **`fontUrl`**: Must be a valid Google Fonts `<link>` `href` URL. Find fonts at https://fonts.google.com
- **`customCss`**: Plain CSS injected after the base styles. Can override any existing rule.
- **Maximum 3 refinements** per interface. For further changes edit the generated prototype code directly.
- Layout options: `sidebar` | `topnav` | `dashboard` | `split` | `wizard` | `minimal`
- Style options: `modern` | `basic` | `abstract`
