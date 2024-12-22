'use client'

import React from 'react';
import Image from 'next/image';
import plantumlEncoder from 'plantuml-encoder';
import { Dialog, DialogContent, DialogTrigger, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { X } from "lucide-react";
import { defaultColors, generateTheme } from '@/lib/plantuml/plantuml-theme';
import { cn } from '@/lib/utils';

interface PlantUMLProps {
  value: string;
  title?: string;
}

const PlantUML: React.FC<PlantUMLProps> = ({ value, title }) => {
  const theme = generateTheme(defaultColors, title);
  
  const scaledValue = `
@startuml
'Apply custom theme
${theme}
scale 1
skinparam dpi 1200
${value.replace('@startuml', '').replace('@enduml', '')}
@enduml
`;

  const encoded = plantumlEncoder.encode(scaledValue);
  const url = `${process.env.NEXT_PUBLIC_PLANTUML_URL}/svg/${encoded}`;

  return (
    <figure className={cn(
      "my-4",
      "rounded-lg",
      "bg-background",
      "dark:bg-[hsl(var(--background))]"
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
                "!shadow-none !rounded-none", // Remove shadow and border
                "hover:opacity-90 transition-opacity" // Add hover effect
              )}
              unoptimized
              sizes="(max-width: 1000px) 100vw, 1000px"
            />
          </div>
        </DialogTrigger>
        <DialogContent className={cn(
          "w-[calc(100vw-4rem)] h-[calc(100vh-4rem)]",
          "max-w-[2560px] max-h-[1600px]",
          "bg-background border-[hsl(var(--border))]",
          "dark:bg-[hsl(var(--background))]"
        )}>
          <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
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
                "!shadow-none !rounded-none" // Remove shadow and border
              )}
              unoptimized
              priority
              sizes="(max-width: 1800px) calc(100vw - 4rem), 1800px"
            />
          </div>
        </DialogContent>
      </Dialog>
      {title && <figcaption className="text-center mt-2 text-muted-foreground">{title}</figcaption>}
    </figure>
  );
};

export default PlantUML; 