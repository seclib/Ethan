"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "@/types";
import { logger } from "@/lib/logger";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, operatorId?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("ethan_token");
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  return headers;
}

function setAuthCookie(token: string) {
  if (typeof window !== "undefined") {
    document.cookie = `ethan_token=${token}; path=/; max-age=86400; SameSite=Lax`;
  }
}

function clearAuthCookie() {
  if (typeof window !== "undefined") {
    document.cookie = "ethan_token=; path=/; max-age=0";
  }
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
          headers: getAuthHeaders(),
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data.user);
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

  const login = async (email: string, password: string, operatorId?: string) => {
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: email, password, operator_id: operatorId }),
        credentials: "include",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Authentication failed");
      }

      const data = await response.json();
      if (data.token || data.access_token) {
        const token = data.token || data.access_token;
        localStorage.setItem("ethan_token", token);
        setAuthCookie(token);
      }
      if (operatorId) {
        localStorage.setItem("ethan_operator_id", operatorId);
      }
      setUser(data.user?.username ? { ...data.user, email: data.user.username } : data.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
        headers: getAuthHeaders(),
      });
    } catch (error) {
      logger.error("Logout error:", error);
    } finally {
      setUser(null);
      localStorage.removeItem("ethan_token");
      clearAuthCookie();
    }
  };

  const refreshToken = async () => {
    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        setUser(null);
      } else {
        const data = await response.json();
        if (data.token || data.access_token) {
          const token = data.token || data.access_token;
          localStorage.setItem("ethan_token", token);
          setAuthCookie(token);
        }
      }
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