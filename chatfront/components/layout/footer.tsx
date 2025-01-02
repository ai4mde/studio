"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Footer() {
  const pathname = usePathname();

  const menuItems = [
    { href: '/contact', label: 'Contact' },
    { href: '/terms', label: 'Terms' },
    { href: '/privacy', label: 'Privacy' },
  ];

  return (
    <footer className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex flex-col items-center gap-4 py-6">
        <div className="flex gap-4 text-sm text-muted-foreground">
          {menuItems.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "transition-colors hover:text-foreground",
                "hover:underline hover:underline-offset-4",
                pathname === href && "font-medium text-primary"
              )}
            >
              {label}
            </Link>
          ))}
        </div>
        <p className="text-center text-sm leading-loose text-muted-foreground">
          Built by{" "}
          AI4MDE Team. The source code is available on{" "}
          <a
            href="https://github.com/ai4mde"
            target="_blank"
            rel="noreferrer"
            className="font-medium text-primary hover:text-primary/90 underline underline-offset-4"
          >
            GitHub
          </a>
          .
        </p>
      </div>
    </footer>
  );
}