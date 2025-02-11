import * as React from "react";
import { json } from "@remix-run/node";
import type { LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { Link, useLoaderData } from "@remix-run/react";
import { promises as fs } from "fs";
import path from "path";
import matter from "gray-matter";
import { Button } from "../components/ui/button";
import { cn } from "../lib/utils";
import { requireUser } from "../services/session.server";
import MaxWidthWrapper from "../components/layout/max-width-wrapper";
import { redirect } from "@remix-run/node";

interface Doc {
  id: string;
  title: string;
  description: string;
  date?: string;
  filename: string;
}

export const meta: MetaFunction = () => {
  return [
    { title: "SRS Documentation - AI4MDE" },
    { description: "Software Requirements Specification documentation for AI4MDE" },
  ];
};

async function getGroupDocuments(groupName: string): Promise<Doc[]> {
  const docsDir = path.join(process.cwd(), 'data', 'liacs', 'srsdocs');
  
  try {
    const files = await fs.readdir(docsDir);
    
    const docs = await Promise.all(
      files
        .filter(file => file.endsWith(".md"))
        .map(async (file) => {
          try {
            const content = await fs.readFile(path.join(docsDir, file), "utf-8");
            const { data, content: docContent } = matter(content);
            
            // Generate an ID from filename if not provided in frontmatter
            const id = data.id || file.replace('.md', '');
            
            // Use filename as title if not provided in frontmatter
            const title = data.title || file.replace('.md', '').replace(/-/g, ' ');
            
            // Generate description from content if not provided
            const description = data.description || docContent.slice(0, 150) + '...';

            return {
              id,
              title,
              description,
              date: data.date || new Date().toISOString(),
              filename: file,
            };
          } catch (error) {
            console.error(`Error reading file ${file}:`, error);
            return null;
          }
        })
    );

    return docs
      .filter((doc): doc is NonNullable<typeof doc> => doc !== null)
      .sort((a, b) => {
        if (!a.date || !b.date) return 0;
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      });
  } catch (error) {
    console.error(`Error accessing directory ${docsDir}:`, error);
    return [];
  }
}

export async function loader({ request }: LoaderFunctionArgs) {
  try {
    const user = await requireUser(request);
    
    if (!user.group_name) {
      throw new Response("User group not found", { status: 403 });
    }

    const docs = await getGroupDocuments(user.group_name);

    return json(
      { docs },
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
      return redirect("/login?redirectTo=/srsdocs");
    }
    throw error;
  }
}

function DocCard({ doc }: { doc: Doc }) {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        <h3 className="text-2xl font-semibold leading-none tracking-tight mb-2">
          {doc.title}
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          {doc.description}
        </p>
        {doc.date && (
          <p className="text-xs text-muted-foreground mb-4">
            {new Date(doc.date).toLocaleDateString()}
          </p>
        )}
        <Button asChild>
          <Link to={`/srsdoc/${doc.id}`}>Read More</Link>
        </Button>
      </div>
    </div>
  );
}

export default function SrsDocs() {
  const { docs } = useLoaderData<typeof loader>();

  return (
    <MaxWidthWrapper className="py-8">
      <h1 className="text-4xl font-bold mb-6">SRS Documentation</h1>
      {docs.length === 0 ? (
        <div className="text-center text-muted-foreground">
          <p>No SRS documents found.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc) => (
            <DocCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </MaxWidthWrapper>
  );
} 