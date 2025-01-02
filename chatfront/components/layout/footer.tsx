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
    <footer className="border-t py-6">
      <div className="container flex flex-col items-center gap-4">
        <div className="flex gap-4 text-sm text-muted-foreground">
          {menuItems.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "transition-colors hover:text-foreground",
                pathname === href && "font-bold text-primary"
              )}
            >
              {label}
            </Link>
          ))}
        </div>
        <p className="text-center text-sm leading-loose text-muted-foreground">
          Built by{" "}
          {/* <a
            href="https://ai4mde.org/team"
            target="_blank"
            rel="noreferrer"
            className="font-medium underline underline-offset-4"
          >
            AI4MDE Team
          </a> */}
          AI4MDE Team. The source code is available on{" "}
          <a
            href="https://github.com/ai4mde"
            target="_blank"
            rel="noreferrer"
            className="font-medium underline underline-offset-4"
          >
            GitHub
          </a>
          .
        </p>
      </div>
    </footer>
  );
}