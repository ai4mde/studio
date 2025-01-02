import React from "react";
import { buttonVariants } from "@/components/ui/button";
import fs, { readFileSync } from "fs";
import matter from "gray-matter";
import Link from "next/link";
import { Metadata } from "next";
import SiteConfig from "@/config/site";
import { cn } from "@/lib/utils";
import { getServerSession } from "@/auth";

interface DocType {
  id: string;
  title: string;
  description: string;
}

const DocList = async () => {
  const session = await getServerSession();
  if (!session?.user?.username) {
    throw new Error("User not authenticated");
  }

  const userPath = `data/${session.user.username.toLowerCase()}/srsdocs`;
  
  if (!fs.existsSync(userPath)) {
    fs.mkdirSync(userPath, { recursive: true });
  }

  const dirContent = fs.readdirSync(userPath, "utf-8");

  const docs: DocType[] = dirContent
    .filter(file => file.endsWith('.md'))
    .map((file) => {
      const fileContent = readFileSync(`${userPath}/${file}`, "utf-8");
      const { data } = matter(fileContent);
      return {
        id: data.id,
        title: data.title,
        description: data.description,
      };
    });

  return (
    <div className="container mx-auto p-4">
      <h1 className={cn(
        "text-3xl font-bold mb-6 text-center my-2",
        "text-foreground"
      )}>
        Your Software Requirements Specifications Documents
      </h1>
      
      {docs.length === 0 ? (
        <div className={cn(
          "text-center py-12",
          "text-muted-foreground"
        )}>
          No documents found. Start a chat to create your first SRS document.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {docs.map((doc: DocType, index: number) => (
            <div 
              key={index} 
              className={cn(
                "rounded-lg overflow-hidden",
                "bg-card text-card-foreground",
                "border border-border",
                "shadow-sm transition-all duration-200",
                "hover:shadow-md hover:border-border/80"
              )}
            >
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-3 text-foreground">
                  {doc.title}
                </h2>
                <p className="mb-4 text-muted-foreground">
                  {doc.description}
                </p>
                <Link
                  href={`/srsdoc/${doc.id}`}
                  className={cn(
                    buttonVariants({ variant: "default" }),
                    "w-full justify-center",
                    "bg-primary hover:bg-primary/90",
                    "text-primary-foreground"
                  )}
                >
                  Open Document
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const metadata: Metadata = {
  title: SiteConfig.title,
  description: SiteConfig.description,
};

export default DocList;

