"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "./AuthProvider";
import { fetchSites } from "../lib/api/client";
import type { SEOSite } from "../lib/api/types";

interface OperatorContextResult {
  loading: boolean;
  error: string | null;
  token: string;
  businessId: string;
  sites: SEOSite[];
  selectedSiteId: string | null;
  setSelectedSiteId: (siteId: string) => void;
  refreshSites: () => Promise<SEOSite[]>;
}

export function useOperatorContext(): OperatorContextResult {
  const router = useRouter();
  const { token, principal, clearSession } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sites, setSites] = useState<SEOSite[]>([]);
  const [selectedSiteId, setSelectedSiteIdState] = useState<string | null>(null);

  const loadSites = useCallback(
    async (accessToken: string, businessId: string): Promise<SEOSite[]> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchSites(accessToken, businessId);
        setSites(response.items);
        setSelectedSiteIdState((current) => {
          if (current && response.items.some((site) => site.id === current)) {
            return current;
          }
          return response.items.length > 0 ? response.items[0].id : null;
        });
        return response.items;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load SEO sites.";
        if (message.includes("Unauthorized") || message.includes("HTTP 401")) {
          clearSession();
          router.push("/");
          return [];
        }
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [clearSession, router],
  );

  useEffect(() => {
    if (!token || !principal) {
      clearSession();
      router.push("/");
      return;
    }
    const accessToken = token;
    const businessId = principal.business_id;

    async function runLoad() {
      try {
        await loadSites(accessToken, businessId);
      } catch {
        // Error state is already managed in loadSites.
      }
    }

    void runLoad();
  }, [clearSession, loadSites, principal, router, token]);

  const refreshSites = useCallback(async (): Promise<SEOSite[]> => {
    if (!token || !principal) {
      clearSession();
      router.push("/");
      return [];
    }
    return loadSites(token, principal.business_id);
  }, [clearSession, loadSites, principal, router, token]);

  return {
    loading,
    error,
    token: token || "",
    businessId: principal?.business_id || "",
    sites,
    selectedSiteId,
    setSelectedSiteId: setSelectedSiteIdState,
    refreshSites,
  };
}
