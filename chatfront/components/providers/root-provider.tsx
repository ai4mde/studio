'use client';

import { ThemeProvider } from "./theme-provider";
import { SessionTimeoutProvider } from "./session-timeout-provider";

export function RootProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <div className="relative flex min-h-screen flex-col">
        {children}
        <SessionTimeoutProvider />
      </div>
    </ThemeProvider>
  );
} 