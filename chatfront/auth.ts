import NextAuth from "next-auth"
import type { NextAuthConfig } from "next-auth"
import type { DefaultSession } from "next-auth"
import type { DefaultJWT } from "next-auth/jwt"
import CredentialsProvider from "next-auth/providers/credentials"
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Add type declarations
declare module "next-auth" {
  interface User {
    id?: string
    username: string
    access_token?: string
    email?: string | null
    name?: string | null
  }
  
  interface Session extends DefaultSession {
    access_token: string
    error?: string
    user: {
      id: string
      username: string
    } & DefaultSession["user"]
  }
}

declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    access_token?: string
    expires_at?: number
    error?: string
    username?: string
  }
}

// Add near the top of the file, after the imports
const TOKEN_EXPIRATION_TIME = 1800; // 30 minutes in seconds

export const authOptions: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null;

        try {
          const formData = new URLSearchParams();
          formData.append('username', credentials.username as string);
          formData.append('password', credentials.password as string);

          const res = await fetch(`${process.env.AUTH_API_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData.toString(),
          });

          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || 'Authentication failed');

          // Get user data after successful login
          const userRes = await fetch(`${process.env.AUTH_API_URL}/api/v1/auth/status`, {
            headers: {
              'Authorization': `Bearer ${data.access_token}`
            }
          });

          if (!userRes.ok) throw new Error('Failed to get user data');
          const userData = await userRes.json();

          return {
            id: userData.id.toString(),
            username: userData.username,
            access_token: data.access_token,
          };
        } catch (error) {
          console.error('Auth error:', error);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      if (account && user) {
        return {
          ...token,
          access_token: user.access_token,
          username: user.username,
          expires_at: Math.floor(Date.now() / 1000 + TOKEN_EXPIRATION_TIME),
        }
      }

      // Check expiration
      const expires_at = token.expires_at || 0;
      if (Date.now() < expires_at * 1000) {
        return token;
      }

      // Token expired, try to refresh
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.access_token}`
          }
        });

        const refreshedTokens = await response.json();
        if (!response.ok) throw refreshedTokens;

        return {
          ...token,
          access_token: refreshedTokens.access_token,
          expires_at: Math.floor(Date.now() / 1000 + TOKEN_EXPIRATION_TIME)
        }
      } catch (error) {
        return { ...token, error: "RefreshAccessTokenError" }
      }
    },
    
    async session({ session, token }) {
      if (token.error === "RefreshAccessTokenError") {
        console.log('Session has refresh error, should logout');
      }
      if (token) {
        session.access_token = token.access_token as string
        session.error = token.error
        session.user.username = token.username as string
      }
      return session
    }
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: TOKEN_EXPIRATION_TIME,
  },
  trustHost: true,
} satisfies NextAuthConfig

const nextAuth = NextAuth(authOptions)

export const { auth, signIn, signOut } = nextAuth
export const { GET, POST } = nextAuth.handlers

// Helper function for server components
export async function getServerSession() {
  return await auth()
}

export async function authenticatedRoute(
  request: NextRequest,
  handler: (req: NextRequest) => Promise<NextResponse>
) {
  const session = await auth()
  
  if (!session) {
    return new NextResponse(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  return handler(request)
} 