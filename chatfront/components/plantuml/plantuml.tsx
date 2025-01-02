'use client'

import React from 'react';
import Image from 'next/image';
import plantumlEncoder from 'plantuml-encoder';
import { Dialog, DialogContent, DialogTrigger, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { X } from "lucide-react";
import { defaultColors, generateTheme } from '@/lib/plantuml/plantuml-theme';
import { cn } from '@/lib/utils';
import { useTheme } from 'next-themes';

interface PlantUMLProps {
  value: string;
  title?: string;
}

const PlantUML: React.FC<PlantUMLProps> = ({ value, title }) => {
  const { theme: currentTheme } = useTheme();
  const isDark = currentTheme === 'dark';

  // Use theme-specific colors
  const themeColors = {
    ...defaultColors,
    backgroundColor: isDark ? '#24273a' : '#eff1f5',  // bg-background
    textColor: isDark ? '#cad3f5' : '#4c4f69',       // text-foreground
    lineColor: isDark ? '#8aadf4' : '#1e66f5',       // primary color
    borderColor: isDark ? '#494d64' : '#4c4f69',     // border
    accentColor: isDark ? '#8aadf4' : '#1e66f5',     // primary
  };
  
  const plantUmlTheme = generateTheme(themeColors, title);
  
  const scaledValue = `
@startuml
'Apply custom theme
${plantUmlTheme}
scale 1
skinparam dpi 1200
skinparam backgroundColor transparent
skinparam DefaultFontColor ${themeColors.textColor}
skinparam ArrowColor ${themeColors.accentColor}
skinparam BorderColor ${themeColors.borderColor}

'Default styles for all diagrams
skinparam {
  FontColor ${themeColors.textColor}
  StereotypeFontColor ${themeColors.textColor}
  TitleFontColor ${themeColors.textColor}
  
  Actor {
    FontColor ${themeColors.textColor}
    BorderColor ${themeColors.textColor}
  }
  
  Participant {
    FontColor ${themeColors.textColor}
    BorderColor ${themeColors.borderColor}
  }
  
  ClassBackgroundColor ${themeColors.backgroundColor}
  ClassBorderColor ${themeColors.borderColor}
  ClassFontColor ${themeColors.textColor}
  
  ActivityBackgroundColor ${themeColors.backgroundColor}
  ActivityBorderColor ${themeColors.borderColor}
  ActivityFontColor ${themeColors.textColor}
  ActivityArrowColor ${themeColors.accentColor}
  
  UsecaseBackgroundColor ${themeColors.backgroundColor}
  UsecaseBorderColor ${themeColors.borderColor}
  UsecaseFontColor ${themeColors.textColor}
  UsecaseArrowColor ${themeColors.accentColor}
  UsecaseActorBorderColor ${themeColors.textColor}
  UsecaseActorFontColor ${themeColors.textColor}
  
  SequenceGroupBackgroundColor ${themeColors.backgroundColor}
  SequenceGroupBorderColor ${themeColors.borderColor}
  SequenceGroupFontColor ${themeColors.textColor}
  SequenceArrowColor ${themeColors.accentColor}
  SequenceLifeLineColor ${themeColors.accentColor}
  SequenceActorBorderColor ${themeColors.textColor}
  SequenceActorFontColor ${themeColors.textColor}
  
  PackageBackgroundColor ${themeColors.backgroundColor}
  PackageBorderColor ${themeColors.borderColor}
  PackageFontColor ${themeColors.textColor}
}

${value.replace('@startuml', '').replace('@enduml', '')}
@enduml
`;

  const encoded = plantumlEncoder.encode(scaledValue);
  const url = `${process.env.NEXT_PUBLIC_PLANTUML_URL}/svg/${encoded}`;

  return (
    <figure className={cn(
      "my-4",
      "rounded-lg",
      "bg-card",
      "p-4"
    )}>
      <Dialog>
        <DialogTrigger asChild>
          <div className="w-full max-w-[1000px] mx-auto relative h-[600px] cursor-pointer">
            <Image
              src={url}
              alt={title || "PlantUML diagram"}
              fill
              className={cn(
                "object-contain plantuml",
                "hover:opacity-90 transition-opacity",
                "!border-none"
              )}
              unoptimized
              sizes="(max-width: 1000px) 100vw, 1000px"
            />
          </div>
        </DialogTrigger>
        <DialogContent className={cn(
          "w-[calc(100vw-4rem)] h-[calc(100vh-4rem)]",
          "max-w-[2560px] max-h-[1600px]",
          "bg-background",
          "border-border"
        )}>
          <DialogClose className={cn(
            "absolute right-4 top-4 rounded-sm",
            "opacity-70 hover:opacity-100",
            "transition-opacity",
            "focus:outline-none focus:ring-2",
            "focus:ring-ring focus:ring-offset-2",
            "disabled:pointer-events-none",
            "data-[state=open]:bg-accent",
            "data-[state=open]:text-muted-foreground"
          )}>
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogClose>
          <DialogTitle className="sr-only">
            {title || 'PlantUML Diagram'} - Enlarged View
          </DialogTitle>
          <div className="relative w-full h-full">
            <Image
              src={url}
              alt={title || "PlantUML diagram (enlarged)"}
              fill
              className={cn(
                "object-contain plantuml",
                "!border-none"
              )}
              unoptimized
              priority
              sizes="(max-width: 1800px) calc(100vw - 4rem), 1800px"
            />
          </div>
        </DialogContent>
      </Dialog>
      {title && (
        <figcaption className="text-center mt-2 text-muted-foreground">
          {title}
        </figcaption>
      )}
    </figure>
  );
};

export default PlantUML; 