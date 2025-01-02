import { Metadata } from 'next';
import Markdown from 'markdown-to-jsx';
import MaxWidthWrapper from '@/components/layout/max-width-wrapper';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Our terms of service and usage conditions',
};

const content = `
## 1. Acceptance of Terms
These Terms of Service ("Terms") govern your use of the Requirements Engineering Automation Tool ("the Tool"), a research project developed as part of a university thesis study.

## 2. Academic Research Purpose
2.1 You acknowledge that:
- This Tool is part of academic research
- It is a proof of concept
- It will be available only during the research phase
- The findings will be published in an academic thesis

2.2 By using this Tool, you agree to:
- Participate in academic research
- Allow your usage data to be analyzed for research purposes
- Be contacted regarding the research if necessary

## 3. Account Registration and Use

### 3.1 Registration Requirements
To use the Tool, you must:
- Provide accurate registration information
- Be authorized to participate on behalf of your company
- Be at least 18 years old
- Have the capacity to agree to these Terms

### 3.2 Usage Guidelines
You agree to:
- Use only fictitious project scenarios
- Not input any sensitive or confidential company information
- Use the Tool for test purposes only
- Not attempt to reverse engineer the Tool
- Not use the Tool for any commercial purposes

## 4. Intellectual Property

### 4.1 Ownership
- The Tool and its original content remain the property of [University Name]
- Research findings belong to the research project
- You retain ownership of your input data
- The source code is available at [your-repository-url]

### 4.2 Licensing
- The Tool is released under the MIT License
- You may use, modify, and distribute the code according to the MIT License terms
- No commercial use of the research data or findings is permitted
- No redistribution rights are granted for research data

## 5. Disclaimers and Limitations

### 5.1 Research Nature
- The Tool is experimental in nature
- No guarantees of accuracy or reliability are made
- The Tool is provided "as is" without warranty

### 5.2 Availability
- Access may be terminated at any time
- The Tool will be discontinued after research completion
- No guarantee of continuous availability

## 6. Data Usage

### 6.1 Research Data
You grant permission for:
- Collection of usage data
- Analysis of interaction patterns
- Publication of anonymized findings

### 6.2 Publication
- Research results will be published
- You may opt for anonymity in publications
- Aggregate data may be used in academic contexts

## 7. Termination

### 7.1 Your Rights
You may:
- Stop participating at any time
- Request deletion of your data
- Withdraw from the research study

### 7.2 Our Rights
We may:
- Terminate access without notice
- Remove accounts that violate these terms
- Discontinue the Tool upon research completion

## 8. Changes to Terms
- Terms may be updated during the research
- Users will be notified of significant changes
- Continued use implies acceptance of changes

## 9. Liability
- No liability for data loss or damages
- No responsibility for misuse of the Tool
- Users responsible for their input data

## 10. Contact
For questions about these Terms, contact:

[Your Name]
[University Department]
[University Name]
Email: [your.email@university.edu]

## 11. Duration
These Terms are effective from [Start Date] until the completion of the thesis project (estimated [End Date]).

## 12. Governing Law
These Terms are governed by the laws of [Your Country/State] and the policies of [University Name].
`;

export default function Terms() {
  return (
    <MaxWidthWrapper className="px-4">
      <h1 className="text-4xl font-bold text-foreground mb-8">Terms of Service</h1>
      <div className="prose prose-lg max-w-none 
        prose-headings:text-foreground
        prose-p:text-foreground
        prose-strong:text-foreground
        prose-ul:text-foreground
        prose-li:text-foreground
        prose-a:text-primary
        prose-a:no-underline
        hover:prose-a:text-primary/80
        hover:prose-a:underline
        prose-hr:border-border
        [&_p]:leading-tight 
        [&_li]:leading-tight 
        [&>*+*]:mt-3
        [&_h2]:mb-3
        [&_h2]:text-foreground
        [&_h3]:mb-2
        [&_h3]:text-foreground
        [&_ul]:!mt-4
        [&_ul]:!mb-4
        [&_ul_li]:!my-2
        dark:prose-invert">
        <Markdown>{content}</Markdown>
      </div>
    </MaxWidthWrapper>
  );
}