import { NextResponse, type NextRequest } from 'next/server'
import { auth } from '@/auth'

// Define public paths that don't require authentication
const PUBLIC_PATHS = [
  '/',
  '/login',
  '/guide',
  '/contact',
  '/terms',
  '/privacy',
] as const

// Define static paths to exclude from middleware
const STATIC_PATHS = [
  '_next/static',
  '_next/image',
  'favicon.ico',
  'public'
] as const

export default auth((req: NextRequest & { auth?: any }) => {
  const { pathname } = req.nextUrl
  const isLoggedIn = !!req.auth

  // Skip middleware for static paths
  if (STATIC_PATHS.some(path => pathname.startsWith(`/${path}`))) {
    return NextResponse.next()
  }

  // Allow public paths
  if (PUBLIC_PATHS.some(path => pathname.startsWith(path))) {
    return NextResponse.next()
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    const loginUrl = new URL('/login', req.url)
    loginUrl.searchParams.set('callbackUrl', encodeURI(pathname))
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
})

// Static matcher configuration for Next.js 15
export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public|login|guide|contact|terms|privacy).*)',
  ]
} 