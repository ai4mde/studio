import * as React from "react"
import type { Metadata } from "next"
import "./globals.css"
import { cn } from "@/lib/utils"
import { fonts } from '@/styles/fonts'
import { SessionProvider } from "@/components/providers/session-provider"
import { RootProvider } from "@/components/providers/root-provider"
import { Header } from "@/components/layout/header"
import { FooterWrapper } from "@/components/layout/footer-wrapper"
import { matrixStyles } from '@/components/ui/matrix-styles'

export const metadata: Metadata = {
  title: "AI4MDE",
  description: "AI-powered Model-Driven Engineering",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(
        matrixStyles.layout.base,
        fonts.sans.className
      )}>
        <div className={matrixStyles.layout.gradient} />
        <SessionProvider>
          <RootProvider>
            <Header />
            <main className="flex-1">
              {children}
            </main>
            <FooterWrapper />
          </RootProvider>
        </SessionProvider>
      </body>
    </html>
  )
}
