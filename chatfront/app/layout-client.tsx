'use client';

import { ThemeProvider } from "@/components/providers/theme-provider"
import { SessionProvider } from "@/components/providers/session-provider"
import { Header } from "@/components/layout/header"
import { FooterWrapper } from "@/components/layout/footer-wrapper"
import { InactivityProvider } from "@/components/providers/inactivity-provider"

export function RootLayoutClient({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SessionProvider>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <InactivityProvider>
          <div className="relative flex min-h-screen flex-col">
            <Header />
            <main className="flex-1">
              {children}
            </main>
            <FooterWrapper />
          </div>
        </InactivityProvider>
      </ThemeProvider>
    </SessionProvider>
  );
} 