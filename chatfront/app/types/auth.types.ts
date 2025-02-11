export interface CustomUser {
  id: string;
  username: string;
  group_name: string;
  access_token: string;
  token_type: string;
  user?: {
    id: string;
    username: string;
    group_name: string;
  };
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  id: string;
  username: string;
  group_name: string;
  access_token: string;
  token_type: string;
}
