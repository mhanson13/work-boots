"use client";

import Script from "next/script";
import { useCallback, useEffect, useRef } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void;
          renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

interface GoogleSignInProps {
  clientId: string;
  onCredential: (credential: string) => void;
}

export function GoogleSignIn({ clientId, onCredential }: GoogleSignInProps) {
  const renderedRef = useRef(false);
  const retryTimeoutRef = useRef<number | null>(null);

  const initializeButton = useCallback((): boolean => {
    if (!clientId || renderedRef.current) {
      return true;
    }

    const googleId = window.google?.accounts?.id;
    const el = document.getElementById("google-signin-button");
    if (!googleId || !el) {
      return false;
    }

    try {
      googleId.initialize({
        client_id: clientId,
        callback: (response: { credential?: string }) => {
          if (response.credential) {
            onCredential(response.credential);
          }
        },
        auto_select: false,
      });
      googleId.renderButton(el, {
        type: "standard",
        size: "large",
        theme: "outline",
        text: "signin_with",
        shape: "pill",
      });
      renderedRef.current = true;
      return true;
    } catch (error) {
      console.error("Google Sign-In button render failed.", error);
      return true;
    }
  }, [clientId, onCredential]);

  useEffect(() => {
    if (!clientId || renderedRef.current) {
      return;
    }

    let attempts = 0;
    const maxAttempts = 20;

    const attemptInitialize = () => {
      if (initializeButton()) {
        return;
      }
      attempts += 1;
      if (attempts >= maxAttempts) {
        console.error("Google Sign-In failed to initialize: GIS script not ready.");
        return;
      }
      retryTimeoutRef.current = window.setTimeout(attemptInitialize, 150);
    };

    attemptInitialize();

    return () => {
      if (retryTimeoutRef.current !== null) {
        window.clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, [clientId, initializeButton]);

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={() => {
          initializeButton();
        }}
        onError={() => {
          console.error("Google Identity Services script failed to load.");
        }}
      />
      <div id="google-signin-button" />
    </>
  );
}
