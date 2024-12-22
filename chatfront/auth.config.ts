import type { NextAuthConfig } from "next-auth"
import Credentials from "next-auth/providers/credentials"
import { JWT } from "next-auth/jwt"
import type { Session } from "next-auth"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    tokenType?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string
    tokenType?: string
  }
}

export const authConfig = {
  providers: [
    Credentials({
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        const { username, password } = credentials as {
          username: string
          password: string
        }
        
        try {
          const response = await fetch('http://localhost:8000/api/v1/auth/login', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
          })

          if (!response.ok) {
            return null
          }

          const data = await response.json()
          
          return {
            id: username,
            name: username,
            email: username,
            username: username,
            accessToken: data.access_token,
            tokenType: data.token_type
          }
        } catch (error) {
          console.error('Auth error:', error)
          return null
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }: { token: JWT; user: any }) {
      if (user) {
        token.accessToken = user.accessToken
        token.tokenType = user.tokenType
      }
      return token
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      session.accessToken = token.accessToken
      session.tokenType = token.tokenType
      return session
    }
  },
  pages: {
    signIn: '/login',
  }
} satisfies NextAuthConfig 