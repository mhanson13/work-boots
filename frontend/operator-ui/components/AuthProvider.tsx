"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { AuthPrincipal } from "../lib/api/types";

const STORAGE_ACCESS_TOKEN = "workboots.operator.access_token";
const STORAGE_PRINCIPAL = "workboots.operator.principal";
const LEGACY_STORAGE_TOKEN = "workboots.operator.token";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  principal: AuthPrincipal | null;
  setSession: (token: string, principal: AuthPrincipal, refreshToken?: string | null) => void;
  clearSession: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

function readStoredPrincipal(raw: string | null): AuthPrincipal | null {
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AuthPrincipal;
  } catch {
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(STORAGE_PRINCIPAL);
    }
    return null;
  }
}

function readStoredSession(): { token: string | null; principal: AuthPrincipal | null } {
  if (typeof window === "undefined") {
    return { token: null, principal: null };
  }
  const storedToken = window.sessionStorage.getItem(STORAGE_ACCESS_TOKEN);
  const storedPrincipal = readStoredPrincipal(window.sessionStorage.getItem(STORAGE_PRINCIPAL));
  return {
    token: storedToken || null,
    principal: storedPrincipal,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readStoredSession().token);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [principal, setPrincipal] = useState<AuthPrincipal | null>(() => readStoredSession().principal);

  useEffect(() => {
    // Remove legacy persistent storage key from prior client versions.
    window.localStorage.removeItem(LEGACY_STORAGE_TOKEN);
  }, []);

  const value = useMemo<AuthState>(() => {
    return {
      token,
      refreshToken,
      principal,
      setSession: (nextToken: string, nextPrincipal: AuthPrincipal, nextRefreshToken?: string | null) => {
        setToken(nextToken);
        setPrincipal(nextPrincipal);
        setRefreshToken(nextRefreshToken || null);
        window.sessionStorage.setItem(STORAGE_ACCESS_TOKEN, nextToken);
        window.sessionStorage.setItem(STORAGE_PRINCIPAL, JSON.stringify(nextPrincipal));
      },
      clearSession: () => {
        setToken(null);
        setRefreshToken(null);
        setPrincipal(null);
        window.sessionStorage.removeItem(STORAGE_ACCESS_TOKEN);
        window.sessionStorage.removeItem(STORAGE_PRINCIPAL);
      },
    };
  }, [token, refreshToken, principal]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("AuthProvider is required.");
  }
  return value;
}
