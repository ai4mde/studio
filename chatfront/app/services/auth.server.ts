import { Authenticator } from "remix-auth";
import { FormStrategy } from "remix-auth-form";
import { sessionStorage } from "./session.server";
import type { CustomUser } from "../types/auth.types";

// Create an instance of the authenticator
export const authenticator = new Authenticator<CustomUser>(sessionStorage, {
  sessionKey: "user", // key for storing the user in the session
  sessionErrorKey: "error", // key for storing error messages
});

// Configure the form strategy
authenticator.use(
  new FormStrategy(async ({ form }) => {
    const username = form.get("username") as string;
    const password = form.get("password") as string;

    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    try {
      console.log('Attempting login for user:', username);
      
      // Create form data for OAuth2 password flow
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "Accept": "application/json"
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error('Login failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });
        
        if (errorData?.detail) {
          throw new Error(errorData.detail);
        }
        throw new Error(`Login failed: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Login response:', data);
      
      if (!data.access_token) {
        console.error('Invalid response data:', data);
        throw new Error("Invalid response from server");
      }

      // Create the user object from the response data
      const user: CustomUser = {
        id: data.id || username,
        username: data.username || username,
        group_name: data.group_name,
        access_token: data.access_token,
        token_type: (data.token_type || 'bearer').charAt(0).toUpperCase() + (data.token_type || 'bearer').slice(1)
      };

      console.log('Created user object:', user);
      return user;
    } catch (error) {
      console.error("Authentication error:", {
        error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      throw error;
    }
  }),
  "form"
);

// Helper function to check if user is authenticated
export async function isAuthenticated(request: Request): Promise<boolean> {
  try {
    const user = await authenticator.authenticate("form", request, {
      failureRedirect: undefined,
    });
    return !!user;
  } catch {
    return false;
  }
}

// Helper function to get authenticated user
export async function getAuthenticatedUser(request: Request): Promise<CustomUser | null> {
  try {
    const clonedRequest = request.clone();
    return await authenticator.authenticate("form", clonedRequest, {
      failureRedirect: undefined,
    });
  } catch {
    return null;
  }
}
