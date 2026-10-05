import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { ApiRequestError, apiRequest } from "../services/api";

export type AuthUser = {
  user_id: string;
  email: string;
  is_active?: boolean;
};

type AuthResponse = {
  authenticated: boolean;
  user: AuthUser;
};

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  busy: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const response = await apiRequest("/api/auth/me");
      const currentUser = await response.json() as AuthUser;
      setUser(currentUser);
      setError(null);
    } catch (requestError) {
      setUser(null);
      setError(requestError instanceof ApiRequestError && requestError.status === 401
        ? null
        : requestError instanceof Error ? requestError.message : "Could not verify your session.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function login(email: string, password: string) {
    setBusy(true);
    setError(null);
    try {
      const response = await apiRequest("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json() as AuthResponse;
      setUser(result.user);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Sign in failed.";
      setError(message);
      throw requestError;
    } finally {
      setBusy(false);
    }
  }

  async function register(email: string, password: string) {
    setBusy(true);
    setError(null);
    try {
      const response = await apiRequest("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json() as AuthResponse;
      setUser(result.user);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Registration failed.";
      setError(message);
      throw requestError;
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    setBusy(true);
    setError(null);
    try {
      await apiRequest("/api/auth/logout", { method: "POST" });
      setUser(null);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Sign out failed.";
      setError(message);
      throw requestError;
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, busy, error, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}