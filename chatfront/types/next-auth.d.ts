import 'next-auth'
import { JWT } from 'next-auth/jwt'

declare module 'next-auth' {
  interface User {
    id: string
    name: string
    email: string
    accessToken: string
    userType: string
    isActive: boolean
    isSuperuser: boolean
  }

  interface Session {
    user: User & {
      accessToken: string
      userType: string
      isActive: boolean
      isSuperuser: boolean
    }
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken?: string
    userType?: string
    isActive?: boolean
    isSuperuser?: boolean
  }
} 

