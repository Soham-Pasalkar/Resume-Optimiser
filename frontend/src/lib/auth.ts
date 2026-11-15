"use client";

import { useEffect, useState } from "react";

export interface UserProfileData {
  headline?: string | null;
  target_role_title?: string | null;
  target_seniority?: string | null;
  years_of_experience?: number | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  preferences?: Record<string, any>;
}

export interface UserData {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  profile?: UserProfileData | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserData;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("careerpilot_access_token");
  if (!token || token === "undefined" || token === "null" || token.trim() === "") {
    return null;
  }
  return token;
}

export function setStoredAuth(data: AuthTokens): void {
  if (typeof window === "undefined") return;
  if (data.access_token) {
    localStorage.setItem("careerpilot_access_token", data.access_token);
  }
  if (data.refresh_token) {
    localStorage.setItem("careerpilot_refresh_token", data.refresh_token);
  }
  if (data.user) {
    localStorage.setItem("careerpilot_user", JSON.stringify(data.user));
  }
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("careerpilot_access_token");
  localStorage.removeItem("careerpilot_refresh_token");
  localStorage.removeItem("careerpilot_user");
}

function parseAuthError(data: any, fallback: string): string {
  if (!data) return fallback;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
  }
  if (data.error?.message) return data.error.message;
  if (data.message) return data.message;
  return fallback;
}

export async function loginUser(email: string, password: string): Promise<AuthTokens> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(parseAuthError(errorData, "Authentication failed. Check your email and password."));
  }
  const data: AuthTokens = await res.json();
  setStoredAuth(data);
  return data;
}

export async function registerUser(email: string, password: string, fullName: string): Promise<AuthTokens> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(parseAuthError(errorData, "Registration failed. Please check your information."));
  }
  const data: AuthTokens = await res.json();
  setStoredAuth(data);
  return data;
}

export async function getCurrentUserProfile(): Promise<UserData | null> {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      if (res.status === 401) {
        clearStoredAuth();
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("careerpilot:unauthorized"));
        }
      }
      return null;
    }
    return await res.json();
  } catch {
    return null;
  }
}

export async function updateUserProfile(updateData: {
  full_name?: string;
  profile?: UserProfileData;
}): Promise<UserData> {
  const token = getStoredToken();
  if (!token) throw new Error("Not authenticated. Please sign in to update your profile.");

  const res = await fetch(`${API_BASE}/users/me`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });

  if (!res.ok) {
    if (res.status === 401) {
      clearStoredAuth();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("careerpilot:unauthorized"));
      }
      throw new Error("Authentication session expired. Please sign in again.");
    }
    const err = await res.json().catch(() => ({}));
    throw new Error(parseAuthError(err, "Failed to update profile"));
  }

  const updatedUser: UserData = await res.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("careerpilot_user", JSON.stringify(updatedUser));
  }
  return updatedUser;
}

// Re-export useAuth from context for backward compatibility
export { useAuth } from "@/context/AuthContext";
