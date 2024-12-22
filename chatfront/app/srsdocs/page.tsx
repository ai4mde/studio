import React from "react";
import { buttonVariants } from "@/components/ui/button";
import fs, { readFileSync } from "fs";
import matter from "gray-matter";
import Link from "next/link";
import { Metadata } from "next";
import SiteConfig from "@/config/site";
import { cn } from "@/lib/utils";

interface DocType {
  id: string;
  title: string;
  description: string;
}

const dirContent = fs.readdirSync("content", "utf-8");

const docs: DocType[] = dirContent.map((file) => {
  const fileContent = readFileSync(`content/${file}`, "utf-8");
  const { data } = matter(fileContent);
  const value: DocType = {
    id: data.id,
    title: data.title,
    description: data.description,
  };
  return value;
});

const DocList = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className={cn(
        "text-3xl font-bold mb-6 text-center my-2",
        "text-foreground"
      )}>
        Your Software Requirements Specifications Documents
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {docs.map((doc: DocType, index: number) => (
          <div key={index} className={cn(
            "shadow-lg rounded-lg overflow-hidden",
            "bg-card text-card-foreground",
            "border border-[hsl(var(--border))]"
          )}>
            <div className="p-4">
              <h2 className="text-xl font-semibold mb-2">{doc.title}</h2>
              <p className="mb-4 text-muted-foreground">{doc.description}</p>
              <Link
                href={`/srsdoc/${doc.id}`}
                className={buttonVariants({ 
                  variant: "default",
                  className: "bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary-hover))] text-primary-foreground"
                })}
              >
                Open Document
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const metadata: Metadata = {
  title: SiteConfig.title,
  description: SiteConfig.description,
};

export default DocList;

