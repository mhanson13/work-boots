"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { GoogleSignIn } from "../components/GoogleSignIn";
import { useAuth } from "../components/AuthProvider";
import { exchangeGoogleIdToken } from "../lib/api/client";

export default function LoginPage() {
  const router = useRouter();
  const { setSession, principal } = useAuth();
  const [idToken, setIdToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  const handleExchange = useCallback(
    async (tokenValue: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await exchangeGoogleIdToken(tokenValue);
        setSession(result.access_token, result.principal, result.refresh_token);
        router.push("/dashboard");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Authentication failed.");
      } finally {
        setLoading(false);
      }
    },
    [router, setSession],
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!idToken.trim()) {
      setError("Google id_token is required.");
      return;
    }
    await handleExchange(idToken.trim());
  };

  useEffect(() => {
    if (principal) {
      setRedirecting(true);
      router.push("/dashboard");
    }
  }, [principal, router]);

  if (redirecting) {
    return (
      <section className="auth-shell">
        <div className="auth-card auth-card-compact">
          <div className="auth-status">
            <span className="spinner" aria-hidden="true" />
            <p>Finalizing your Operator Workspace session...</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="auth-shell">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-badge">MBSRN Operator Workspace</p>
          <h1>Sign in to manage SEO operations</h1>
          <p className="auth-subtitle">
            Use your approved Google identity to access business-scoped operator tooling, reviews,
            and recommendation workflows.
          </p>
        </div>

        <div className="auth-section">
          <p className="auth-section-title">Preferred sign-in</p>
          <GoogleSignIn
            clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ""}
            onCredential={(credential) => {
              void handleExchange(credential);
            }}
          />
        </div>

        <form onSubmit={(event) => void handleSubmit(event)} className="auth-section stack">
          <label htmlFor="idToken">Manual Google ID token exchange (fallback)</label>
          <input
            id="idToken"
            value={idToken}
            onChange={(event) => setIdToken(event.target.value)}
            placeholder="Paste Google id_token"
          />
          <button className="primary" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Exchange Token"}
          </button>
        </form>

        {error ? <p className="auth-error">{error}</p> : null}
      </div>
    </section>
  );
}
