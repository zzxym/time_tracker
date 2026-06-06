/** React Router configuration. */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import AppLayout from '../components/layout/AppLayout';
import HomePage from '../pages/HomePage';
import TimelinePage from '../pages/TimelinePage';
import StatsPage from '../pages/StatsPage';
import TagsPage from '../pages/TagsPage';
import SettingsPage from '../pages/SettingsPage';
import LoginPage from '../components/auth/LoginPage';
import RegisterPage from '../components/auth/RegisterPage';
import { useWebSocket } from '../hooks/useWebSocket';
import { manageSyncMode } from '../services/syncService';
import { useSyncStore } from '../stores/syncStore';

/** Protected route wrapper that requires authentication. */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

/** Public route wrapper that redirects if already authenticated. */
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (isAuthenticated) {
    return <Navigate to="/home" replace />;
  }
  return <>{children}</>;
};

/** Main router component with all routes defined. */
const AppRouter: React.FC = () => {
  // Initialize WebSocket connection when authenticated
  const { connectionStatus } = useWebSocket();

  // Manage sync mode (polling fallback)
  React.useEffect(() => {
    manageSyncMode(connectionStatus);
  }, [connectionStatus]);

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />

      {/* Protected routes with layout */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/home" replace />} />
                <Route path="/home" element={<HomePage />} />
                <Route path="/timeline" element={<TimelinePage />} />
                <Route path="/stats" element={<StatsPage />} />
                <Route path="/tags" element={<TagsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<Navigate to="/home" replace />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default AppRouter;
