import { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  interface Session {
    access_token: string;
    user: {
      id: string;
      username: string;
    } & DefaultSession['user'];
  }

  interface User {
    id: string;
    username: string;
    name?: string;
    email?: string;
  }
} 

