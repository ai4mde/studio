import { NextResponse } from 'next/server'
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

export default auth((req) => {
  const isLoggedIn = !!req.auth
  const { pathname } = req.nextUrl

  // Allow public paths
  if (PUBLIC_PATHS.some(path => pathname.startsWith(path))) {
    return NextResponse.next()
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    const url = new URL('/login', req.url)
    url.searchParams.set('callbackUrl', encodeURI(pathname))
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
})

// Configure matcher to exclude static paths
export const config = {
  matcher: [
    `/((?!${STATIC_PATHS.join('|')}|${PUBLIC_PATHS.join('|')}).*)`,
  ],
} 