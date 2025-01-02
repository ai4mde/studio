import { Metadata } from 'next';
import Markdown from 'markdown-to-jsx';
import MaxWidthWrapper from '@/components/layout/max-width-wrapper';

export const metadata: Metadata = {
  title: 'Tutorial',
  description: 'Learn how to use our platform effectively',
};

const content = `
<div style="background: yellow; padding: 10px;">
<h1>🚧 <strong>Attention:</strong> <br>
This page is under construction!</h1>
<h2>Nothing on this page is valid yet.</h2>
</div>

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
      <h1 className="text-4xl font-bold mb-8">Tutorial</h1>
      <div className="prose prose-lg max-w-none 
        [&_p]:leading-tight 
        [&_li]:leading-tight 
        [&>*+*]:mt-3
        [&_h2]:mb-3
        [&_h3]:mb-2
        [&_ul]:mt-2
        [&_ul]:mb-2">
        <Markdown>{content}</Markdown>
      </div>
    </MaxWidthWrapper>
  );
}