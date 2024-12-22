import colors from 'tailwindcss/colors'

export const defaultColors = {
  primary: colors.sky[600],      // brand blue (light mode)
  secondary: colors.red[500],    // brand red (light mode)
  accent: colors.sky[500],       // lighter primary
  background: colors.slate[50],  // light background
  border: colors.slate[200],     // light border
  text: colors.slate[800],       // dark text
} as const;

export const darkColors = {
  primary: colors.sky[400],      // lighter blue for dark mode
  secondary: colors.red[400],    // lighter red for dark mode
  accent: colors.sky[300],       // lighter accent
  background: colors.slate[900], // dark background
  border: colors.slate[700],     // dark border
  text: colors.slate[100],       // light text
} as const;

export interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  border: string;
  text: string;
  arrow: string;
  header: string;
}

export function generateTheme(colors = defaultColors, title?: string) {
  return `
${title ? `title ${title}\n` : ''}
!$PRIMARY = "${colors.primary}"
!$SECONDARY = "${colors.secondary}"
!$ACCENT = "${colors.accent}"
!$BACKGROUND = "${colors.background}"
!$BORDER = "${colors.border}"
!$TEXT = "${colors.text}"

' Font settings
skinparam defaultFontName "Geist Sans"
skinparam defaultFontSize 14
skinparam defaultFontColor $TEXT

skinparam backgroundColor transparent
skinparam useBetaStyle false

' Font settings per element type
skinparam classFontName "Geist Sans"
skinparam packageFontName "Geist Sans"
skinparam activityFontName "Geist Sans"
skinparam sequenceFontName "Geist Sans"
skinparam componentFontName "Geist Sans"
skinparam noteFontName "Geist Mono"
skinparam stereotypeFontName "Geist Sans"

' Title and header fonts
skinparam titleFontName "Geist Sans"
skinparam titleFontSize 16
skinparam titleFontStyle bold
skinparam headerFontName "Geist Sans"
skinparam headerFontSize 14

${generateBaseTheme(colors)}
`
}

function generateBaseTheme(_colors: typeof defaultColors) {
  return `
skinparam sequence {
  ArrowColor $PRIMARY
  LifeLineBorderColor $SECONDARY
  LifeLineBackgroundColor $BACKGROUND
  BoxBorderColor $BORDER
  BoxBackgroundColor $BACKGROUND
  DividerBorderColor $BORDER
  DividerBackgroundColor $BACKGROUND
  GroupBorderColor $BORDER
  GroupBackgroundColor $BACKGROUND
}

skinparam class {
  BorderColor $PRIMARY
  BackgroundColor $BACKGROUND
  ArrowColor $ACCENT
  StereotypeFontColor $SECONDARY
}

skinparam component {
  BorderColor $PRIMARY
  BackgroundColor $BACKGROUND
  ArrowColor $ACCENT
  InterfaceBackgroundColor $BACKGROUND
  InterfaceBorderColor $BORDER
}

skinparam note {
  BorderColor $BORDER
  BackgroundColor $BACKGROUND
}`
} 