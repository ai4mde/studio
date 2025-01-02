"use client"

import { usePathname, useRouter } from "next/navigation"
import { Home, MessageCircle, Map, FileText, PencilRuler, LucideIcon } from "lucide-react"
import { useSession, signOut } from "next-auth/react"

interface User {
  id: string
  name?: string
  username?: string
  email?: string
}

interface NavigationItem {
  name: string
  href: string
  protected?: boolean
  icon: LucideIcon
  description?: string
}

export function useNavigation() {
  const { data: session, status } = useSession()
  const pathname = usePathname()
  const router = useRouter()

  const studioUrl = process.env.NEXT_PUBLIC_STUDIO_URL || '#'

  const navigation: NavigationItem[] = [
    { 
      name: 'Home', 
      href: '/', 
      icon: Home, 
      protected: false,
      description: 'Return to homepage'
    },
    { 
      name: 'Chat', 
      href: '/chat', 
      protected: true, 
      icon: MessageCircle,
      description: 'Chat with AI assistant'
    },
    { 
      name: 'Guide', 
      href: '/guide', 
      icon: Map, 
      protected: false,
      description: 'Learn how to use the platform'
    },
    { 
      name: 'SRSDoc', 
      href: '/srsdocs', 
      protected: true, 
      icon: FileText,
      description: 'View documentation'
    },
    { 
      name: 'Studio', 
      href: studioUrl, 
      icon: PencilRuler,
      description: 'Open design studio'
    },
  ]

  const isActivePath = (path: string) => pathname?.startsWith(path)

  const handleProtectedLink = (e: React.MouseEvent<Element>, href: string) => {
    e.preventDefault()
    if (!session && href) {
      router.push(`/login?callbackUrl=${encodeURIComponent(href)}`)
    } else {
      router.push(href)
    }
  }

  const handleLogout = async () => {
    await signOut({
      redirect: true,
      callbackUrl: '/login'
    })
  }

  return {
    navigation,
    isActivePath,
    handleProtectedLink,
    handleLogout,
    isAuthenticated: status === 'authenticated' && !!session,
    isLoading: status === 'loading',
    user: session?.user as User
  }
}

export type { NavigationItem, User }