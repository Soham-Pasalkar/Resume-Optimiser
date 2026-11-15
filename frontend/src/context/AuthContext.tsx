"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import {
  UserData,
  AuthTokens,
  getStoredToken,
  setStoredAuth,
  clearStoredAuth,
  getCurrentUserProfile,
} from "@/lib/auth";

export type AuthStatus = "INITIALIZING" | "AUTHENTICATED" | "UNAUTHENTICATED";

export interface AuthContextType {
  user: UserData | null;
  token: string | null;
  status: AuthStatus;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (tokens: AuthTokens) => void;
  register: (tokens: AuthTokens) => void;
  logout: () => void;
  refreshUser: () => Promise<UserData | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserData | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthStatus>("INITIALIZING");

  const initAuth = useCallback(async () => {
    if (typeof window === "undefined") return;

    const storedToken = getStoredToken();
    if (!storedToken || storedToken === "undefined" || storedToken === "null") {
      clearStoredAuth();
      setToken(null);
      setUser(null);
      setStatus("UNAUTHENTICATED");
      return;
    }

    setToken(storedToken);
    try {
      const profile = await getCurrentUserProfile();
      if (profile) {
        setUser(profile);
        setStatus("AUTHENTICATED");
      } else {
        clearStoredAuth();
        setToken(null);
        setUser(null);
        setStatus("UNAUTHENTICATED");
      }
    } catch {
      clearStoredAuth();
      setToken(null);
      setUser(null);
      setStatus("UNAUTHENTICATED");
    }
  }, []);

  useEffect(() => {
    initAuth();

    // Listen to custom unauthorized events from API client
    const handleUnauthorized = () => {
      clearStoredAuth();
      setToken(null);
      setUser(null);
      setStatus("UNAUTHENTICATED");
    };

    // Listen to storage changes across tabs
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "careerpilot_access_token") {
        initAuth();
      }
    };

    window.addEventListener("careerpilot:unauthorized", handleUnauthorized);
    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("careerpilot:unauthorized", handleUnauthorized);
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [initAuth]);

  const login = (tokens: AuthTokens) => {
    setStoredAuth(tokens);
    setToken(tokens.access_token);
    setUser(tokens.user);
    setStatus("AUTHENTICATED");
  };

  const register = (tokens: AuthTokens) => {
    setStoredAuth(tokens);
    setToken(tokens.access_token);
    setUser(tokens.user);
    setStatus("AUTHENTICATED");
  };

  const logout = () => {
    clearStoredAuth();
    setToken(null);
    setUser(null);
    setStatus("UNAUTHENTICATED");
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  const refreshUser = async (): Promise<UserData | null> => {
    try {
      const updated = await getCurrentUserProfile();
      if (updated) {
        setUser(updated);
        setStatus("AUTHENTICATED");
      }
      return updated;
    } catch {
      return null;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        status,
        isLoading: status === "INITIALIZING",
        isAuthenticated: status === "AUTHENTICATED",
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
