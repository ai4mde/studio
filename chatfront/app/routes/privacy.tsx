import * as React from "react";
import type { MetaFunction } from "@remix-run/node";
import Markdown from "markdown-to-jsx";
import MaxWidthWrapper from "../components/layout/max-width-wrapper";

export const meta: MetaFunction = () => {
  return [
    { title: "Privacy Policy - AI4MDE" },
    { name: "description", content: "Privacy policy and data handling practices" },
  ];
};

const content = `
## 1. Introduction
This privacy policy applies to the Requirements Engineering Automation Tool ("the Tool"), which is part of a university thesis project. This Tool is a proof of concept and will be available for a limited time during the research phase.

## 2. Information We Collect
We collect the following personal information when you register to use our Tool:
- First name and last name
- Professional email address
- Phone number
- Job description
- Company name

### 2.1 Research Data
The Tool collects data about how requirements engineering processes are conducted. We explicitly request that users:
- Use fictitious project scenarios
- Do not input any sensitive or confidential company information
- Use the Tool only for test purposes

## 3. How We Use Your Information

### 3.1 Primary Use
Your information is used for:
- Creating and managing your account
- Communication regarding the research project
- Analysis of the requirements engineering process
- Documentation in the thesis research

### 3.2 Research Publication
- Research findings will be published in the university thesis
- You have the option to remain anonymous in any research publications
- Aggregated data may be used for academic purposes

## 4. Data Protection and Storage

### 4.1 Data Security
- All data is stored securely using industry-standard encryption
- Access to personal data is strictly limited to the research team
- Data will be deleted after the completion of the thesis project

### 4.2 Data Retention
- All collected data will be retained only for the duration of the research project
- Upon completion of the thesis, personal data will be deleted
- Anonymized research findings may be retained for academic purposes

## 5. Your Rights
You have the right to:
- Access your personal data
- Request correction of your data
- Request deletion of your data
- Opt for anonymity in research publications
- Withdraw from the research at any time

## 6. Third-Party Access
- No personal data will be shared with third parties
- Anonymized research findings may be shared in academic contexts
- The tool may use essential third-party services for hosting and functionality

## 7. Research Ethics
This research project follows the ethical guidelines of [Your University Name] and has been approved by [relevant ethics committee if applicable].

## 8. Contact Information
For any questions about this privacy policy or the research project, please contact:

[Your Name]
[University Department]
[University Name]
Email: [your.email@university.edu]

## 9. Changes to This Policy
We may update this privacy policy during the course of the research. Users will be notified of any significant changes.

## 10. Duration
This privacy policy is effective from [Start Date] until the completion of the thesis project (estimated [End Date]).
`;

export default function Privacy() {
  return (
    <MaxWidthWrapper className="px-4 py-10">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
      <div className="prose prose-lg max-w-none dark:prose-invert
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