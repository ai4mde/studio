import * as React from "react";
import { json, redirect } from "@remix-run/node";
import type { LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { Link, useLoaderData } from "@remix-run/react";
import { promises as fs } from "fs";
import path from "path";
import matter from "gray-matter";
import Markdown from "markdown-to-jsx";
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css';
import MaxWidthWrapper from "../components/layout/max-width-wrapper";
import { requireUser } from "../services/session.server";
import { Button } from "../components/ui/button";
import { Dialog, DialogContent } from "../components/ui/dialog";
import { ChevronLeft, ZoomIn } from "lucide-react";
import { cn } from "../lib/utils";
import { convertPlantUmlToSvg } from "../utils/plantuml.server";

interface DocData {
  id: string;
  title: string;
  description: string;
  date?: string;
  filename: string;
}

interface Doc {
  content: string;
  data: DocData;
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  if (!data?.doc) {
    return [
      { title: "Document Not Found - AI4MDE" },
      { description: "The requested SRS document could not be found." },
    ];
  }

  return [
    { title: `${data.doc.data.title} - AI4MDE` },
    { description: data.doc.data.description },
  ];
};

async function getDocument(id: string): Promise<Doc | null> {
  const docsDir = path.join(process.cwd(), 'data', 'liacs', 'srsdocs');
  
  try {
    const files = await fs.readdir(docsDir);
    const mdFiles = files.filter(file => file.endsWith('.md'));
    
    for (const file of mdFiles) {
      const content = await fs.readFile(path.join(docsDir, file), 'utf-8');
      const { data: frontMatter, content: docContent } = matter(content);
      
      const fileId = frontMatter.id || file.replace('.md', '');
      if (fileId === id) {
        return {
          content: docContent,
          data: {
            id: fileId,
            title: frontMatter.title || file.replace('.md', '').replace(/-/g, ' '),
            description: frontMatter.description || docContent.slice(0, 150) + '...',
            date: frontMatter.date || new Date().toISOString(),
            filename: file,
          },
        };
      }
    }
    
    return null;
  } catch (error) {
    console.error('Error reading document:', error);
    return null;
  }
}

export async function loader({ request, params }: LoaderFunctionArgs) {
  try {
    const user = await requireUser(request);
    
    if (!user.group_name) {
      throw new Response("User group not found", { status: 403 });
    }

    const doc = await getDocument(params.id || '');
    
    if (!doc) {
      throw new Response("Document not found", { status: 404 });
    }

    // Process the content to find and convert PlantUML diagrams
    const content = await processPlantUml(doc.content);

    return json(
      { doc: { ...doc, content } },
      {
        headers: {
          'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      }
    );
  } catch (error) {
    // Redirect to login if authentication fails
    if (error instanceof Response && error.status === 401) {
      return redirect(`/login?redirectTo=/srsdoc/${params.id}`);
    }
    throw error;
  }
}

// Add components for enlargeable elements
function DiagramImage({ src, alt }: { src: string; alt: string }) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <>
      <div 
        onClick={() => setIsOpen(true)}
        className="relative group cursor-zoom-in"
      >
        <img 
          src={src} 
          alt={alt} 
          className="max-w-full h-auto my-4 mx-auto rounded-lg shadow-md transition-opacity group-hover:opacity-95" 
          loading="lazy"
        />
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="bg-background/80 p-2 rounded-full">
            <ZoomIn className="w-6 h-6 text-foreground" />
          </div>
        </div>
      </div>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0">
          <div className="w-full h-full overflow-auto p-6">
            <img 
              src={src} 
              alt={alt} 
              className="w-full h-full object-contain"
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Add new component for clickable tables
function EnlargeableTable({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <>
      <div
        onClick={() => setIsOpen(true)}
        className="relative group cursor-zoom-in overflow-auto"
      >
        <div className="my-4">
          {children}
        </div>
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="bg-background/80 p-2 rounded-full">
            <ZoomIn className="w-6 h-6 text-foreground" />
          </div>
        </div>
      </div>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0">
          <div className="w-full h-full overflow-auto p-6">
            {children}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Add new component for enlargeable code blocks
function EnlargeableCode({ language, children, html }: { language: string; children: string; html: string }) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <>
      <div
        onClick={() => setIsOpen(true)}
        className="relative group cursor-zoom-in"
      >
        <pre className="!p-0 !m-0 !bg-transparent mb-10">
          <code
            className={`block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : 'hljs'}`}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </pre>
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="bg-background/80 p-2 rounded-full">
            <ZoomIn className="w-6 h-6 text-foreground" />
          </div>
        </div>
      </div>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0">
          <div className="w-full h-full overflow-auto p-6">
            <pre className="!p-0 !m-0 !bg-transparent">
              <code
                className={`block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : 'hljs'}`}
                dangerouslySetInnerHTML={{ __html: html }}
              />
            </pre>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Update CodeBlock to use EnlargeableCode
function CodeBlock({ className = "", children }: { className?: string; children: string }) {
  const language = className.replace(/language-/, '');
  const html = React.useMemo(() => {
    if (language && hljs.getLanguage(language)) {
      try {
        return hljs.highlight(children, { language }).value;
      } catch (err) {
        console.error('Error highlighting code:', err);
      }
    }
    return hljs.highlightAuto(children).value;
  }, [children, language]);

  return (
    <EnlargeableCode language={language} html={html} children={children} />
  );
}

async function processPlantUml(content: string): Promise<string> {
  const plantUmlRegex = /```plantuml\n([\s\S]*?)```/g;
  let match;
  let processedContent = content;
  let diagramCount = 0;
  
  while ((match = plantUmlRegex.exec(content)) !== null) {
    const [fullMatch, diagramCode] = match;
    const svgUrl = await convertPlantUmlToSvg(diagramCode);
    if (svgUrl) {
      diagramCount++;
      processedContent = processedContent.replace(
        fullMatch,
        `<div data-diagram="${diagramCount}" data-url="${svgUrl}"></div>`
      );
    }
  }
  
  return processedContent;
}

const markdownOptions = {
  options: {
    forceBlock: true,
    forceWrapper: true,
    wrapper: 'div',
    disableParsingRawHTML: false,
    escapeHtml: false,
  },
  overrides: {
    h1: { props: { className: "text-3xl font-bold mt-8 mb-4" } },
    h2: { props: { className: "text-2xl font-semibold mt-6 mb-3" } },
    h3: { props: { className: "text-xl font-semibold mt-4 mb-2" } },
    h4: { props: { className: "text-lg font-semibold mt-4 mb-2" } },
    p: { props: { className: "text-muted-foreground mb-4" } },
    ul: { props: { className: "list-disc list-inside mb-4 ml-4" } },
    ol: { props: { className: "list-decimal list-inside mb-4 ml-4" } },
    li: { props: { className: "mb-1" } },
    a: { props: { className: "text-primary hover:underline" } },
    blockquote: { props: { className: "border-l-4 border-primary pl-4 italic my-4" } },
    code: {
      component: CodeBlock
    },
    pre: {
      component: ({ children }) => children
    },
    img: { 
      props: { 
        className: "max-w-full h-auto my-4 mx-auto rounded-lg shadow-md",
        loading: "lazy"
      } 
    },
    div: {
      component: ({ 'data-diagram': isDiagram, 'data-url': url, ...props }) => {
        if (isDiagram && url) {
          return <DiagramImage src={url} alt={`Diagram ${isDiagram}`} />;
        }
        return <div {...props} />;
      }
    },
    'plantuml': {
      component: ({ children }) => <div className="hidden">{children}</div>
    },
    table: {
      component: ({ children }) => (
        <EnlargeableTable>
          <table className="w-full border-collapse border border-border">
            {children}
          </table>
        </EnlargeableTable>
      )
    },
    th: {
      props: {
        className: "border border-border bg-muted p-2 text-left font-semibold"
      }
    },
    td: {
      props: {
        className: "border border-border p-2"
      }
    },
  },
};

export default function SrsDoc() {
  const { doc } = useLoaderData<typeof loader>();

  return (
    <MaxWidthWrapper className="py-8">
      <div className="mb-8">
        <Button asChild variant="ghost" size="sm">
          <Link to="/srsdocs" className="flex items-center gap-2">
            <ChevronLeft className="h-4 w-4" />
            Back to Documents
          </Link>
        </Button>
      </div>

      <article className={cn(
        "max-w-none",
        "[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:mb-4",
        "[&>h2]:text-3xl [&>h2]:font-semibold [&>h2]:mb-3 [&>h2]:mt-8",
        "[&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:mt-6",
        "[&>p]:text-muted-foreground [&>p]:mb-4",
        "[&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-4",
        "[&>ol]:list-decimal [&>ol]:ml-6 [&>ol]:mb-4",
        "[&>li]:mb-1",
        "[&>blockquote]:border-l-4 [&>blockquote]:border-primary [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:my-4",
        "[&>pre]:bg-muted [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:mb-4 [&>pre]:overflow-x-auto",
        "[&>code]:bg-muted [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded"
      )}>
        <h1 className="text-4xl font-bold mb-4">{doc.data.title}</h1>
        {doc.data.date && (
          <p className="text-sm text-muted-foreground mb-8">
            {new Date(doc.data.date).toLocaleDateString()}
          </p>
        )}
        <Markdown options={markdownOptions}>{doc.content}</Markdown>
      </article>
    </MaxWidthWrapper>
  );
} 