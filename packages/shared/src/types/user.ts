// User / Auth types
export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  settings: UserSettings;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  auto_pause_enabled: boolean;
  theme: 'light' | 'dark' | 'system';
  default_activity_color: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
}
