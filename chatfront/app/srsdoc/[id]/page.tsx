import MaxWidthWrapper from "@/components/layout/max-width-wrapper";
import React from "react";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeSlug from "rehype-slug";
import matter from "gray-matter";
import fs from "fs";
import TableOfContents from "@/components/layout/table-of-contents";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import { rehypePrettyCode } from "rehype-pretty-code";
import { Metadata } from "next";
import remarkGfm from 'remark-gfm';
import rehypeReact from 'rehype-react';
import PlantUML from '@/components/plantuml/plantuml';
import { visit } from 'unist-util-visit'
import * as runtime from 'react/jsx-runtime'
import rehypeStringify from 'rehype-stringify'
import { cn } from "@/lib/utils";
import { Node } from 'unist'
import type { Options as RehypeReactOptions } from 'rehype-react'
import { getServerSession } from "@/auth";

interface PageProps {
  params: Promise<{ id: string }>
}

interface PlantUMLNode extends Node {
  type: string;
  lang?: string;
  value: string;
  data?: {
    hName: string;
    hProperties: {
      value: string;
      title?: string;
    };
  };
}

function remarkPlantuml() {
  return (tree: Node) => {
    visit(tree, 'code', (node: PlantUMLNode) => {
      if (node.lang === 'plantuml') {
        const firstLine = node.value.split('\n')[0];
        const titleMatch = firstLine.match(/^#\s*Title:\s*(.+)$/);
        const title = titleMatch ? titleMatch[1] : undefined;
        const value = titleMatch ? node.value.split('\n').slice(1).join('\n') : node.value;
        
        node.type = 'plantuml'
        node.data = {
          hName: 'plantuml',
          hProperties: {
            value: value.trim(),
            title
          }
        }
      }
    })
    return tree;
  }
}

const rehypeOptions: Partial<RehypeReactOptions> = {
  components: {
    plantuml: PlantUML,
  },
  Fragment: React.Fragment,
  jsx: runtime.jsx,
  jsxs: runtime.jsxs
}

const prettyCodeOptions = {
  theme: {
    dark: 'github-dark',
    light: 'github-light',
  },
  keepBackground: true,
  grid: true,
  showLineNumbers: true,
  defaultLang: 'plaintext'
} as const

export default async function Page({ params }: PageProps) {
  const { id } = await params;

  // Get user session
  const session = await getServerSession();
  if (!session?.user?.username) {
    throw new Error("User not authenticated");
  }

  // Get content from user-specific filesystem path
  const userPath = `data/${session.user.username.toLowerCase()}/srsdocs`;
  const filePath = `${userPath}/${id}.md`;
  
  try {
    const fileContent = fs.readFileSync(filePath, "utf-8");
    const { content } = matter(fileContent);

    const jsxProcessor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkPlantuml)
      .use(remarkRehype, { allowDangerousHtml: true })
      .use(rehypeSlug)
      .use(rehypePrettyCode, prettyCodeOptions)
      .use(rehypeAutolinkHeadings)
      .use(rehypeReact, rehypeOptions);

    const htmlProcessor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkRehype, { allowDangerousHtml: true })
      .use(rehypeSlug)
      .use(rehypeAutolinkHeadings)
      .use(rehypeStringify);

    const [jsxContent, htmlContent] = await Promise.all([
      jsxProcessor.process(content),
      htmlProcessor.process(content)
    ]);

    return (
      <MaxWidthWrapper className="py-8">
        <div className={cn(
          "container py-8 mx-auto",
          "w-full",
          "min-h-screen",
          "flex gap-8"
        )}>
          <div className="flex flex-1">
            <div className={cn(
              "px-8 md:px-16 prose dark:prose-invert max-w-none",
              "w-full",
              "prose-headings:text-foreground prose-headings:scroll-mt-20",
              "prose-p:text-muted-foreground",
              "prose-pre:bg-[hsl(var(--muted))]",
              "prose-pre:border prose-pre:border-[hsl(var(--border))]",
              "prose-code:text-[hsl(var(--primary))]",
              "prose-a:text-[hsl(var(--primary))] prose-a:no-underline hover:prose-a:underline",
              "[&_img]:rounded-md [&_img:not(.plantuml)]:shadow-md",
              "prose-hr:border-[hsl(var(--border))]",
              "prose-strong:text-foreground",
              "prose-ul:text-muted-foreground prose-ol:text-muted-foreground",
              "prose-blockquote:text-muted-foreground prose-blockquote:border-[hsl(var(--primary))]",
              "[&_p]:leading-tight",
              "[&_li]:leading-tight",
              "[&>*+*]:mt-3",
              "[&_h2]:mb-3",
              "[&_h3]:mb-2",
              "[&_ul]:mt-0.5",
              "[&_ul]:mb-0.5"
            )}>
              {jsxContent.result}
            </div>
            <TableOfContents
              className={cn(
                "text-sm w-[300px]",
                "sticky top-20",
                "self-start"
              )}
              htmlContent={String(htmlContent)}
            />
          </div>
        </div>
      </MaxWidthWrapper>
    );
  } catch (error) {
    console.error(`Error reading file: ${filePath}`, error);
    throw new Error("Document not found or access denied");
  }
}

export async function generateMetadata(
  { params }: { params: Promise<{ id: string }> }
): Promise<Metadata> {
  const { id } = await params;
  
  // Get user session
  const session = await getServerSession();
  if (!session?.user?.username) {
    throw new Error("User not authenticated");
  }

  const userPath = `data/${session.user.username.toLowerCase()}/srsdocs`;
  const filePath = `${userPath}/${id}.md`;
  
  try {
    const fileContent = fs.readFileSync(filePath, "utf-8");
    const { data } = matter(fileContent);

    return {
      title: data.title,
      description: data.description,
    };
  } catch (error) {
    console.error(`Error reading metadata: ${filePath}`, error);
    return {
      title: "Document Not Found",
      description: "The requested document could not be found",
    };
  }
}