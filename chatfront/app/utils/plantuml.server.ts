import { encode } from 'plantuml-encoder';

const PLANTUML_SERVER = 'https://www.plantuml.com/plantuml/svg';

// Theme configuration for PlantUML diagrams
const THEME_SETTINGS = `
skinparam backgroundColor transparent
skinparam useBetaStyle false

skinparam defaultFontName Inter
skinparam defaultFontSize 12

skinparam sequence {
  ArrowColor hsl(var(--primary))
  LifeLineBorderColor hsl(var(--muted))
  LifeLineBackgroundColor hsl(var(--background))
  ParticipantBorderColor hsl(var(--primary))
  ParticipantBackgroundColor hsl(var(--background))
  ParticipantFontColor hsl(var(--foreground))
  ActorBorderColor hsl(var(--primary))
  ActorBackgroundColor hsl(var(--background))
  ActorFontColor hsl(var(--foreground))
}

skinparam class {
  BackgroundColor hsl(var(--background))
  BorderColor hsl(var(--primary))
  ArrowColor hsl(var(--primary))
  FontColor hsl(var(--foreground))
  AttributeFontColor hsl(var(--muted-foreground))
  StereotypeFontColor hsl(var(--accent))
}

skinparam component {
  BackgroundColor hsl(var(--background))
  BorderColor hsl(var(--primary))
  ArrowColor hsl(var(--primary))
  FontColor hsl(var(--foreground))
}

skinparam interface {
  BackgroundColor hsl(var(--background))
  BorderColor hsl(var(--primary))
  FontColor hsl(var(--foreground))
}

skinparam note {
  BackgroundColor hsl(var(--accent))
  BorderColor hsl(var(--accent-foreground))
  FontColor hsl(var(--accent-foreground))
}
`;

export async function convertPlantUmlToSvg(plantUmlCode: string): Promise<string> {
  try {
    // Remove any ```plantuml and ``` markers
    const cleanCode = plantUmlCode
      .replace(/```plantuml/g, '')
      .replace(/```/g, '')
      .trim();

    // Inject theme settings at the start of the diagram
    // (after @startuml if present, at the start otherwise)
    const themedCode = cleanCode.includes('@startuml')
      ? cleanCode.replace('@startuml', `@startuml\n${THEME_SETTINGS}`)
      : `@startuml\n${THEME_SETTINGS}\n${cleanCode}\n@enduml`;

    // Encode the PlantUML code
    const encoded = encode(themedCode);

    // Return the URL to the SVG
    return `${PLANTUML_SERVER}/${encoded}`;
  } catch (error) {
    console.error('Error converting PlantUML to SVG:', error);
    return '';
  }
} 