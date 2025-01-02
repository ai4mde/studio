import { Metadata } from 'next';
import Markdown from 'markdown-to-jsx';
import MaxWidthWrapper from '@/components/layout/max-width-wrapper';
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle } from "lucide-react";

export const metadata: Metadata = {
  title: 'Tutorial',
  description: 'Learn how to use our platform effectively',
};

const content = `
# Getting Started Tutorial

## 1. Creating Your Account
Learn how to set up your account and profile.

### 1.1 Sign Up Process
Step-by-step guide to creating your account.

### 1.2 Profile Setup
Customize your profile and preferences.

## 2. Basic Features

### 2.1 Navigation
Learn how to navigate through the platform.

### 2.2 Key Functions
Overview of essential features and tools.

## 3. Advanced Features

### 3.1 Advanced Tools
Explore powerful features for power users.

### 3.2 Customization
Personalize your experience.

## 4. Best Practices
Tips and tricks for getting the most out of our platform.

## 5. Need Help?
Contact our support team for assistance.
`;

export default function Tutorial() {
  return (
    <MaxWidthWrapper className="px-4">
      <h1 className="text-4xl font-bold text-foreground mb-8">Tutorial</h1>
      
      <Alert className="mb-8 border-primary bg-primary/5">
        <AlertTriangle className="h-5 w-5 text-primary" />
        <AlertTitle className="text-foreground font-semibold">
          Under Construction
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          This page is currently being developed. The content shown here is placeholder text.
        </AlertDescription>
      </Alert>

      <div className="prose prose-lg max-w-none 
        prose-headings:text-foreground
        prose-p:text-foreground
        prose-strong:text-foreground
        prose-ul:text-foreground
        prose-li:text-foreground
        prose-a:text-primary
        prose-a:no-underline
        hover:prose-a:underline
        hover:prose-a:text-primary/80
        prose-hr:border-border
        [&_p]:leading-relaxed
        [&_li]:leading-relaxed
        [&>*+*]:mt-4
        [&_h2]:mb-4
        [&_h2]:text-foreground
        [&_h3]:mb-3
        [&_h3]:text-foreground
        [&_ul]:my-2
        [&_ol]:my-2
        dark:prose-invert">
        <Markdown>{content}</Markdown>
      </div>
    </MaxWidthWrapper>
  );
}