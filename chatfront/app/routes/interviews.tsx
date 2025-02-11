import * as React from "react";
import { json, redirect } from "@remix-run/node";
import type { LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { Link, useLoaderData } from "@remix-run/react";
import { promises as fs } from "fs";
import path from "path";
import matter from "gray-matter";
import MaxWidthWrapper from "../components/layout/max-width-wrapper";
import { requireUser } from "../services/session.server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { FileText } from "lucide-react";

export const meta: MetaFunction = () => {
  return [
    { title: "Interview Logs - AI4MDE" },
    { description: "Interview logs and transcripts for AI4MDE project" },
  ];
};

interface Interview {
  id: string;
  title: string;
  description: string;
  date: string;
  filename: string;
}

async function getGroupInterviews(groupName: string): Promise<Interview[]> {
  const interviewsDir = path.join(process.cwd(), 'data', groupName, 'interviews');
  
  try {
    const files = await fs.readdir(interviewsDir);
    const mdFiles = files.filter(file => file.endsWith('.md'));
    
    const interviews = await Promise.all(
      mdFiles.map(async (file) => {
        const content = await fs.readFile(path.join(interviewsDir, file), 'utf-8');
        const { data: frontMatter, content: interviewContent } = matter(content);
        
        return {
          id: frontMatter.id || file.replace('.md', ''),
          title: frontMatter.title || file.replace('.md', '').replace(/-/g, ' '),
          description: frontMatter.description || interviewContent.slice(0, 150) + '...',
          date: frontMatter.date || new Date().toISOString(),
          filename: file,
        } as Interview;
      })
    );
    
    return interviews.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  } catch (error) {
    console.error('Error reading interviews:', error);
    return [];
  }
}

export async function loader({ request }: LoaderFunctionArgs) {
  try {
    const user = await requireUser(request);
    
    if (!user.group_name) {
      throw new Response("User group not found", { status: 403 });
    }

    const interviews = await getGroupInterviews(user.group_name);
    
    return json(
      { interviews },
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
      return redirect("/login?redirectTo=/interviews");
    }
    throw error;
  }
}

function InterviewCard({ id, title, description, date }: { id: string; title: string; description: string; date: string }) {
  return (
    <Card className="group hover:shadow-md transition-shadow">
      <Link to={`/interview/${id}`} className="block h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            {title}
          </CardTitle>
          {date && (
            <CardDescription>
              {new Date(date).toLocaleDateString()}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground line-clamp-3">{description}</p>
        </CardContent>
      </Link>
    </Card>
  );
}

export default function Interviews() {
  const { interviews } = useLoaderData<typeof loader>();

  return (
    <MaxWidthWrapper className="py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Interview Logs</h1>
        <p className="text-muted-foreground">
          Browse interview logs and transcripts for the AI4MDE project.
        </p>
      </div>

      {interviews.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No interview logs found.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {interviews.map((interview) => (
            <InterviewCard key={interview.id} {...interview} />
          ))}
        </div>
      )}
    </MaxWidthWrapper>
  );
} 