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
    dark: 'catppuccin-macchiato',
    light: 'catppuccin-latte',
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
          "w-full min-h-screen",
          "flex gap-8",
          "bg-background"
        )}>
          <div className="flex flex-1">
            <div className={cn(
              "px-8 md:px-16 prose dark:prose-invert max-w-none w-full",
              "prose-headings:text-foreground",
              "prose-headings:scroll-mt-20",
              "prose-p:text-foreground",
              "prose-strong:text-foreground",
              "prose-ul:text-foreground",
              "prose-ol:text-foreground",
              "prose-pre:bg-card",
              "prose-pre:border prose-pre:border-border",
              "prose-pre:shadow-sm",
              "prose-code:text-primary",
              "prose-a:text-primary",
              "prose-a:no-underline",
              "hover:prose-a:underline",
              "hover:prose-a:text-primary/80",
              "[&_img]:rounded-lg",
              "[&_img:not(.plantuml)]:shadow-sm",
              "[&_img:not(.plantuml)]:border",
              "[&_img:not(.plantuml)]:border-border",
              "prose-blockquote:text-muted-foreground",
              "prose-blockquote:border-primary",
              "prose-blockquote:bg-muted/50",
              "prose-table:text-foreground",
              "prose-th:text-foreground",
              "prose-td:text-muted-foreground",
              "prose-hr:border-border",
              "[&_p]:leading-relaxed",
              "[&_li]:leading-relaxed",
              "[&>*+*]:mt-4",
              "[&_h2]:mb-4",
              "[&_h3]:mb-3",
              "[&_ul]:my-2",
              "[&_ol]:my-2",
              "[&_.plantuml]:bg-card",
              "[&_.plantuml]:rounded-lg",
              "[&_.plantuml]:p-4",
              "dark:[&_.plantuml_text]:fill-foreground",
              "dark:[&_.plantuml_path]:stroke-foreground",
              "dark:[&_.plantuml_rect]:stroke-border",
              "[&_.plantuml_img]:max-w-full",
              "[&_.plantuml_img]:h-auto",
              "[&_.plantuml_img]:!border-none"
            )}>
              {jsxContent.result}
            </div>
            <TableOfContents
              className={cn(
                "hidden lg:block",
                "text-sm w-[300px]",
                "sticky top-20 self-start",
                "pl-8 border-l border-border",
                "text-muted-foreground"
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