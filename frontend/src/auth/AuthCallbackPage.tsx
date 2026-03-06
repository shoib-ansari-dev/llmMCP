/**
 * Auth Callback Page
 * Handles OAuth callback (Google login redirect)
 */

import { useEffect, useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { storeTokens } from './api';

interface AuthCallbackPageProps {
  onSuccess: () => void;
  onError: () => void;
}

export function AuthCallbackPage({ onSuccess, onError }: AuthCallbackPageProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const errorParam = params.get('error');

    if (errorParam) {
      setError(errorParam);
      setTimeout(onError, 3000);
      return;
    }

    if (accessToken && refreshToken) {
      // Store tokens
      storeTokens({
        access_token: accessToken,
        refresh_token: refreshToken,
        token_type: 'bearer',
        expires_in: 1800,
      });

      // Clear URL params
      window.history.replaceState({}, document.title, '/');

      // Redirect to app
      onSuccess();
    } else {
      setError('Authentication failed. Missing tokens.');
      setTimeout(onError, 3000);
    }
  }, [onSuccess, onError]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Failed</h2>
          <p className="text-gray-600">{error}</p>
          <p className="text-sm text-gray-500 mt-2">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <Loader2 className="h-12 w-12 text-blue-500 animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Completing sign in...</h2>
        <p className="text-gray-600">Please wait while we log you in.</p>
      </div>
    </div>
  );
}

