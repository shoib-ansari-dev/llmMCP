/**
 * Authentication API Client
 */

import axios from 'axios';
import type {
  User,
  TokenResponse,
  LoginCredentials,
  RegisterData,
  PasswordResetRequest,
  PasswordResetConfirm
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Store tokens in localStorage
 */
export function storeTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

/**
 * Clear tokens from localStorage
 */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Get access token from localStorage
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if dev mode is enabled
 */
export async function checkDevMode(): Promise<boolean> {
  try {
    const response = await authApi.get('/auth/dev-mode');
    return response.data.dev_mode === true;
  } catch {
    return false;
  }
}

/**
 * Register a new user
 */
export async function register(data: RegisterData): Promise<TokenResponse> {
  const response = await authApi.post<TokenResponse>('/auth/register', data);
  storeTokens(response.data);
  return response.data;
}

/**
 * Login with email and password
 */
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await authApi.post<TokenResponse>('/auth/login', credentials);
  storeTokens(response.data);
  return response.data;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  try {
    await authApi.post('/auth/logout');
  } finally {
    clearTokens();
  }
}

/**
 * Get current user
 */
export async function getCurrentUser(): Promise<User> {
  const token = getAccessToken();
  const response = await authApi.get<User>('/auth/me', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return response.data;
}

/**
 * Refresh access token
 */
export async function refreshAccessToken(): Promise<TokenResponse | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await authApi.post<TokenResponse>('/auth/refresh', null, {
      params: { refresh_token: refreshToken },
    });
    storeTokens(response.data);
    return response.data;
  } catch {
    clearTokens();
    return null;
  }
}

/**
 * Request password reset email
 */
export async function forgotPassword(data: PasswordResetRequest): Promise<void> {
  await authApi.post('/auth/forgot-password', data);
}

/**
 * Reset password with token
 */
export async function resetPassword(data: PasswordResetConfirm): Promise<void> {
  await authApi.post('/auth/reset-password', data);
}

/**
 * Get Google OAuth URL
 */
export function getGoogleAuthUrl(): string {
  return `${API_BASE_URL}/auth/google`;
}

/**
 * Setup axios interceptor for token refresh
 */
export function setupAuthInterceptor(): void {
  authApi.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        const newTokens = await refreshAccessToken();
        if (newTokens) {
          originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
          return authApi(originalRequest);
        }
      }

      return Promise.reject(error);
    }
  );
}

