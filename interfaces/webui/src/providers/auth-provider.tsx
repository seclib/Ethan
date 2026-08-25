"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "@/types";
import { logger } from "@/lib/logger";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Cookie management is now handled securely by Next.js API routes (HttpOnly).
// No localStorage or client-side cookie manipulation is needed.

/**
 * Normalize the backend user payload into the full User interface.
 * The backend returns { username, role } but the frontend expects
 * { id, name, email, role, permissions, created_at }.
 */
function normalizeUser(raw: any): User | null {
  if (!raw) return null;
  const username = raw.username || raw.email || raw.name || "unknown";
  return {
    id: raw.id || username,
    name: raw.name || username,
    email: raw.email || username,
    role: raw.role || "user",
    permissions: raw.permissions || [],
    created_at: raw.created_at || new Date().toISOString(),
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch("/api/auth/me", {
          method: "GET",
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          setUser(normalizeUser(data.user));
        } else {
          setUser(null);
        }
      } catch (error) {
        logger.error("Auth check failed:", error);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: email, password }),
        credentials: "include",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.message || "Authentication failed");
      }

      const data = await response.json();
      // The API route handler reads the token from the body and sets
      // the ethan_token HttpOnly cookie on the NextResponse.
      setUser(normalizeUser(data.user));
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      logger.error("Logout error:", error);
    } finally {
      setUser(null);
    }
  };

  const refreshToken = async () => {
    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) {
        setUser(null);
      }
      // Assuming /api/auth/refresh sets the new HttpOnly cookie if successful
    } catch (error) {
      logger.error("Token refresh failed:", error);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}