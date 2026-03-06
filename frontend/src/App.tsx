import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth, LoginPage, RegisterPage, ForgotPage } from './auth';
import { DashboardPage, AuthCallbackPage, ResetPage, ContractIQPage, FinanceDigestPage } from './pages';
import { LandingPage } from './landing';
import './App.css';

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPage />} />
      <Route path="/reset-password" element={<ResetPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={isAuthenticated ? <DashboardPage /> : <Navigate to="/login" />}
      />
      <Route
        path="/contracts"
        element={isAuthenticated ? <ContractIQPage /> : <Navigate to="/login" />}
      />
      <Route
        path="/finance"
        element={isAuthenticated ? <FinanceDigestPage /> : <Navigate to="/login" />}
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
