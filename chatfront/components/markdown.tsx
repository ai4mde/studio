'use client';

import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Card } from '@/components/ui/card'

interface MarkdownProps {
  content: string;
  className?: string;
}

export function Markdown({ content, className }: MarkdownProps) {
  return (
    <ReactMarkdown
      className={cn(
        'prose dark:prose-invert max-w-none',
        'prose-headings:text-foreground',
        'prose-p:text-muted-foreground',
        'prose-strong:text-foreground',
        'prose-a:text-primary hover:prose-a:underline',
        'prose-code:text-foreground prose-code:bg-muted',
        'prose-pre:p-0 prose-pre:bg-transparent',
        'prose-img:rounded-md',
        'prose-hr:border-border',
        className
      )}
      remarkPlugins={[remarkGfm]}
      components={{
        code(props) {
          const { inline, className, children, ...rest } = props
          const match = /language-(\w+)/.exec(className || '')
          const language = match ? match[1] : ''

          if (!inline && language) {
            return (
              <Card className="overflow-hidden">
                <SyntaxHighlighter
                  language={language}
                  style={oneDark}
                  PreTag="div"
                  className="!m-0 rounded-none"
                  showLineNumbers
                  {...rest}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              </Card>
            )
          }

          return (
            <code 
              className={cn(
                'rounded-sm px-1.5 py-0.5',
                'bg-muted text-foreground',
                className
              )} 
              {...rest}
            >
              {children}
            </code>
          )
        }
      }}
    >
      {content}
    </ReactMarkdown>
  )
} 