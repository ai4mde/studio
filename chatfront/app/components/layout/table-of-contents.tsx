import * as React from "react";
import { cn } from "../../lib/utils";

interface TableOfContentsProps {
  className?: string;
  htmlContent: string;
}

export default function TableOfContents({ className, htmlContent }: TableOfContentsProps) {
  const [headings, setHeadings] = React.useState<{ id: string; text: string; level: number }[]>([]);

  React.useEffect(() => {
    if (!htmlContent) return;

    // Create a temporary div to parse the HTML content
    const div = document.createElement("div");
    div.innerHTML = htmlContent;

    // Get all headings (h1-h6)
    const headingElements = div.querySelectorAll("h1, h2, h3, h4, h5, h6");
    const headingsData = Array.from(headingElements).map((heading) => ({
      id: heading.id,
      text: heading.textContent || "",
      level: parseInt(heading.tagName[1]),
    }));

    setHeadings(headingsData);
  }, [htmlContent]);

  if (headings.length === 0) return null;

  return (
    <nav className={cn("hidden xl:block", className)} aria-label="Table of contents">
      <div className="space-y-2">
        <p className="font-medium">On this page</p>
        <ul className="m-0 list-none">
          {headings.map((heading) => (
            <li
              key={heading.id}
              className={cn(
                "mt-0 pt-2",
                heading.level === 1 && "pl-0",
                heading.level === 2 && "pl-4",
                heading.level === 3 && "pl-8",
                heading.level === 4 && "pl-12",
                heading.level === 5 && "pl-16",
                heading.level === 6 && "pl-20"
              )}
            >
              <a
                href={`#${heading.id}`}
                className={cn(
                  "inline-block no-underline",
                  "text-muted-foreground hover:text-foreground",
                  "transition-colors"
                )}
              >
                {heading.text}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
} 