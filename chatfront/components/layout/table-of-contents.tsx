"use client"
import { cn } from '@/lib/utils'
import React, { useEffect, useState } from 'react'

interface LinkType {
  id: string 
  text: string
}

const TableOfContents = ({ htmlContent, className }: { htmlContent: string, className: string }) => {
  const [links, setLinks] = useState<null|LinkType[]>(null);
  const [activeId, setActiveId] = useState<string>('');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: '-20% 0% -35% 0%' }
    );

    const headings = document.querySelectorAll('h2');
    headings.forEach((heading) => observer.observe(heading));

    return () => observer.disconnect();
  }, [links]);

  useEffect(() => {
    const temp = document.createElement("div");
    temp.innerHTML = htmlContent;
    const headings = temp.querySelectorAll('h2');
    const generatedLinks: LinkType[] = [];

    headings.forEach((heading, index) => {
      const id = heading.id || `heading-${index}`;
      heading.id = id;
      
      generatedLinks.push({
        id: id,
        text: (heading as HTMLElement).innerText
      });
    });

    setLinks(generatedLinks);
  }, [htmlContent]);
    
  return (
    <div className={cn('hidden md:block', className)}>
      <nav className={cn(
        "sticky top-20 p-4 ml-4",
        "text-muted-foreground",
        "border rounded-lg border-border",
        "bg-background/60 backdrop-blur-sm",
        className
      )}>
        <h2 className="font-medium mb-4 text-foreground">
          Table of Contents
        </h2>
        <ul className='space-y-1 text-sm'>
          {links && links.map((link) => (
            <li key={link.id}>
              <a 
                href={`#${link.id}`}
                className={cn(
                  'block py-1 px-2 rounded-md',
                  'transition-colors duration-200',
                  'hover:text-primary hover:bg-muted',
                  activeId === link.id 
                    ? 'font-medium text-primary bg-muted' 
                    : 'text-muted-foreground'
                )}
              >
                {link.text.length > 50 
                  ? `${link.text.slice(0, 50)}...` 
                  : link.text
                }
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}

export default TableOfContents