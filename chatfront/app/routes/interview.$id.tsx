import * as React from "react";
import { json } from "@remix-run/node";
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
import { redirect } from "@remix-run/node";

interface InterviewData {
  id: string;
  title: string;
  description: string;
  date?: string;
  filename: string;
}

interface Interview {
  content: string;
  data: InterviewData;
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  if (!data?.interview) {
    return [
      { title: "Interview Not Found - AI4MDE" },
      { description: "The requested interview log could not be found." },
    ];
  }

  return [
    { title: `${data.interview.data.title} - AI4MDE` },
    { description: data.interview.data.description },
  ];
};

async function getInterview(groupName: string, id: string): Promise<Interview | null> {
  const interviewsDir = path.join(process.cwd(), 'data', groupName, 'interviews');
  
  try {
    const files = await fs.readdir(interviewsDir);
    const mdFiles = files.filter(file => file.endsWith('.md'));
    
    for (const file of mdFiles) {
      const content = await fs.readFile(path.join(interviewsDir, file), 'utf-8');
      const { data: frontMatter, content: interviewContent } = matter(content);
      
      const fileId = frontMatter.id || file.replace('.md', '');
      if (fileId === id) {
        return {
          content: interviewContent,
          data: {
            id: fileId,
            title: frontMatter.title || file.replace('.md', '').replace(/-/g, ' '),
            description: frontMatter.description || interviewContent.slice(0, 150) + '...',
            date: frontMatter.date || new Date().toISOString(),
            filename: file,
          },
        };
      }
    }
    
    return null;
  } catch (error) {
    console.error('Error reading interview:', error);
    return null;
  }
}

export async function loader({ request, params }: LoaderFunctionArgs) {
  try {
    const user = await requireUser(request);
    
    if (!user.group_name) {
      throw new Response("User group not found", { status: 403 });
    }

    const interview = await getInterview(user.group_name, params.id || '');
    
    if (!interview) {
      throw new Response("Interview not found", { status: 404 });
    }

    return json(
      { interview },
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
      return redirect(`/login?redirectTo=/interview/${params.id}`);
    }
    throw error;
  }
}

// Add components for enlargeable elements (DiagramImage, EnlargeableTable, EnlargeableCode)
// ... (same components as in srsdoc.$id.tsx) ...

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
    <pre className="!p-0 !m-0 !bg-transparent mb-10">
      <code 
        className={`block p-4 rounded-lg bg-muted overflow-x-auto ${language ? `hljs language-${language}` : 'hljs'}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </pre>
  );
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
  },
};

export default function InterviewLog() {
  const { interview } = useLoaderData<typeof loader>();

  return (
    <MaxWidthWrapper className="py-8">
      <div className="mb-8">
        <Button asChild variant="ghost" size="sm">
          <Link to="/interviews" className="flex items-center gap-2">
            <ChevronLeft className="h-4 w-4" />
            Back to Interviews
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
        <h1 className="text-4xl font-bold mb-4">{interview.data.title}</h1>
        {interview.data.date && (
          <p className="text-sm text-muted-foreground mb-8">
            {new Date(interview.data.date).toLocaleDateString()}
          </p>
        )}
        <Markdown options={markdownOptions}>{interview.content}</Markdown>
      </article>
    </MaxWidthWrapper>
  );
} 