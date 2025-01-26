import NextAuth from "next-auth"
import type { NextAuthConfig } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

// Extend the User type to include our custom fields
declare module "next-auth" {
  interface User {
    username: string
    accessToken: string
    userType: string
    isActive: boolean
    isSuperuser: boolean
  }
  
  interface Session {
    user: User
  }
}

export const config = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // Early validation
        if (!credentials?.username || !credentials?.password) {
          console.error('Missing credentials')
          return null
        }
        
        try {
          const response = await fetch(`${process.env.AUTH_API_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/x-www-form-urlencoded',
              'Accept': 'application/json'
            },
            body: new URLSearchParams({
              username: credentials.username as string,
              password: credentials.password as string,
              grant_type: 'password'
            })
          })

          const data = await response.json()
          
          // Handle non-200 responses
          if (!response.ok) {
            console.error('Authentication failed:', data.detail || 'Unknown error')
            return null
          }

          // Validate response data
          if (!data.access_token || !data.username) {
            console.error('Invalid response data:', data)
            return null
          }

          // Return normalized user data
          return {
            id: data.id.toString(),
            name: data.username,
            email: data.email,
            username: data.username,
            accessToken: data.access_token,
            userType: data.user_type,
            isActive: data.is_active,
            isSuperuser: data.is_superuser
          }
        } catch (error) {
          console.error('Authentication error:', error instanceof Error ? error.message : 'Unknown error')
          return null
        }
      }
    })
  ],
  trustHost: true,
  debug: process.env.NODE_ENV === 'development',
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.accessToken = user.accessToken
      }
      return token
    },
    session: async ({ session, token }) => {
      if (session.user) {
        session.user.accessToken = token.accessToken as string
      }
      return session
    }
  },
  pages: {
    signIn: '/login',
    error: '/login'
  }
} satisfies NextAuthConfig

export const { handlers: { GET, POST }, auth, signIn, signOut } = NextAuth(config)

// Export getServerSession for compatibility
export const getServerSession = auth 