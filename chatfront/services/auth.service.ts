import { User } from "next-auth";
import Cookies from 'js-cookie';

type LoginCredentials = {
  username: string;
  password: string;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
};

export class AuthService {
  private static baseUrl =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/auth";
  private static TOKEN_KEY = 'auth_token';
  private static USER_KEY = 'auth_user';

  static getToken(): string | null {
    return Cookies.get(this.TOKEN_KEY) || null;
  }

  static setToken(token: string): void {
    Cookies.set(this.TOKEN_KEY, token, { expires: 7 }); // 7 days
  }

  static setUser(user: User): void {
    Cookies.set(this.USER_KEY, JSON.stringify(user), { expires: 7 });
  }

  static getUser(): User | null {
    try {
      const user = Cookies.get(this.USER_KEY);
      return user ? JSON.parse(user) : null;
    } catch {
      Cookies.remove(this.USER_KEY);
      return null;
    }
  }

  static clearAuth(): void {
    Cookies.remove(this.TOKEN_KEY);
    Cookies.remove(this.USER_KEY);
  }

  private static async fetchWithAuth(
    endpoint: string,
    options: RequestInit = {},
  ) {
    const token = this.getToken();
    const headers = {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ message: "An error occurred" }));
      throw new Error(
        error.detail || error.message || `HTTP error! status: ${response.status}`,
      );
    }

    return response;
  }

  static async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await fetch(`${this.baseUrl}/login`, {
        method: "POST",
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data: LoginResponse = await response.json();
      this.setToken(data.access_token);
      
      // Get user data
      const userResponse = await this.fetchWithAuth("/status");
      const userData = await userResponse.json();
      this.setUser(userData);
      
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Login failed: ${error.message}`);
      }
      throw new Error('An unexpected error occurred during login');
    }
  }

  static async logout(): Promise<void> {
    try {
      await this.fetchWithAuth("/logout", { method: "POST" });
    } finally {
      this.clearAuth();
    }
  }
}
