"use client"
import { cn } from '@/lib/utils'
import React, {useEffect, useState} from 'react'

interface LinkType{
    id: string 
    text: string
}

const TableOfContents = ({htmlContent, className}: {htmlContent: string, className: string}) => {
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
       temp.innerHTML = htmlContent
        

       // Check this syntax 
       const headings = temp.querySelectorAll('h2');

       const generatedLinks:LinkType[] = [];

       headings.forEach((heading, index)=>{
        const id = heading.id || `heading-${index}`;
        heading.id = id;

        
        generatedLinks.push({
            id: id,
            text: (heading as HTMLElement).innerText
        })
        
    })

    setLinks(generatedLinks);

    }, [htmlContent])
    
  return (
    <div className={cn('hidden md:block ', className)}>
        <nav className={cn(
            "sticky top-20 p-4 ml-4",
            "text-muted-foreground",
            className
        )}>
            <h2 className="font-bold mb-4 text-foreground">Table of Contents</h2>
            <ul className='not-prose text-xs'>
                {links && links.map((link)=>{
                    return <li key={link.id} className='pt-1'>
                        <a 
                            href={`#${link.id}`}
                            className={cn(
                                'hover:text-sky-600 transition-colors',
                                activeId === link.id ? 'font-bold text-sky-600' : 'text-gray-600'
                            )}
                        >
                            {link.text.slice(0, 50)}

                            {(link.text.length > 50) ? "...": ""}


                        </a>
                    </li>
                })}
            </ul>
        </nav>

    </div>
  )
}

export default TableOfContents