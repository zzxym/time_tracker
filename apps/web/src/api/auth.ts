/** Authentication API functions. */

import apiClient from './client';
import type { APIResponse, AuthResponse, LoginRequest, RegisterRequest, TokenPair } from '@time-tracker/shared';

/** Register a new user account. */
export async function registerUser(data: RegisterRequest): Promise<AuthResponse> {
  const response = await apiClient.post<APIResponse<AuthResponse>>('/auth/register', data);
  return response.data.data;
}

/** Login with email and password. */
export async function loginUser(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<APIResponse<AuthResponse>>('/auth/login', data);
  return response.data.data;
}

/** Refresh the access token using a refresh token. */
export async function refreshAccessToken(refreshToken: string): Promise<TokenPair> {
  const response = await apiClient.post<APIResponse<TokenPair>>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data.data;
}

/** Get the current authenticated user's profile. */
export async function getCurrentUser(): Promise<AuthResponse['user']> {
  const response = await apiClient.get<APIResponse<AuthResponse['user']>>('/auth/me');
  return response.data.data;
}
