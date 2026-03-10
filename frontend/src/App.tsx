/**
 * Root application component with routing, auth gating, and query provider.
 */
import { useEffect } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "./store/authStore";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AssetListPage from "./pages/AssetListPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * Layout wrapper that requires authentication.
 * Redirects to /login if the user is not authenticated.
 */
function ProtectedLayout() {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" />
          <p className="mt-3 text-sm text-gray-500">Loading AssetGuard...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top navigation bar */}
      <nav className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-6">
              <a href="/" className="text-lg font-bold text-blue-600">
                AssetGuard
              </a>
              <div className="hidden md:flex items-center gap-4 text-sm">
                <a href="/" className="text-gray-700 hover:text-blue-600">
                  Dashboard
                </a>
                <a href="/assets" className="text-gray-700 hover:text-blue-600">
                  Assets
                </a>
                <a href="/licenses" className="text-gray-700 hover:text-blue-600">
                  Licenses
                </a>
                <a href="/maintenance" className="text-gray-700 hover:text-blue-600">
                  Maintenance
                </a>
                <a href="/vendors" className="text-gray-700 hover:text-blue-600">
                  Vendors
                </a>
                <a href="/reports" className="text-gray-700 hover:text-blue-600">
                  Reports
                </a>
              </div>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-gray-600">
                {useAuthStore.getState().user?.full_name}
              </span>
              <button
                onClick={() => useAuthStore.getState().logout()}
                className="text-gray-500 hover:text-red-600"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page content */}
      <main className="max-w-7xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/assets" element={<AssetListPage />} />
            {/* Additional routes can be added here */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
