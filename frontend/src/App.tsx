import { useEffect, useState } from "react";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import AuthPage from "./pages/AuthPage";
import SearchPage from "./pages/SearchPage";
import { navigate } from "./routes";

function AppRoutes() {
  const { user, loading, error } = useAuth();
  const [pathname, setPathname] = useState(window.location.pathname);

  useEffect(() => {
    const updatePath = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", updatePath);
    return () => window.removeEventListener("popstate", updatePath);
  }, []);

  useEffect(() => {
    if (!loading && user && (pathname === "/login" || pathname === "/register")) navigate("/");
  }, [loading, pathname, user]);

  if (loading) {
    return (
      <main className="auth-loading" aria-live="polite">
        <span className="loading-pulse" />
        <span>Checking your NEXUS session</span>
      </main>
    );
  }

  if (pathname === "/login" || pathname === "/register") {
    return <AuthPage mode={pathname === "/register" ? "register" : "login"} authError={error} />;
  }

  return <SearchPage />;
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;