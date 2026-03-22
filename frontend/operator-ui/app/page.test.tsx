import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import LoginPage from "./page";

const mockPush = jest.fn();
const mockSetSession = jest.fn();
const mockExchangeGoogleIdToken = jest.fn();
const mockUseAuth = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

jest.mock("../components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock("../lib/api/client", () => {
  const actual = jest.requireActual("../lib/api/client");
  return {
    ...actual,
    exchangeGoogleIdToken: (...args: unknown[]) => mockExchangeGoogleIdToken(...args),
  };
});

jest.mock("../components/GoogleSignIn", () => ({
  GoogleSignIn: ({ onCredential }: { onCredential: (credential: string) => void }) => (
    <button onClick={() => onCredential("google-credential")}>Mock Google Sign-In</button>
  ),
}));

beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({
    setSession: mockSetSession,
    principal: null,
  });
  mockExchangeGoogleIdToken.mockResolvedValue({
    access_token: "access-1",
    refresh_token: "refresh-1",
    token_type: "bearer",
    expires_at: "2026-03-23T00:00:00Z",
    refresh_expires_at: "2026-04-22T00:00:00Z",
    auth_source: "google",
    principal: {
      business_id: "biz-1",
      principal_id: "admin-1",
      display_name: "Admin One",
      role: "admin",
      is_active: true,
    },
  });
});

describe("login page", () => {
  it("renders production-ready operator sign-in copy", () => {
    render(<LoginPage />);

    expect(screen.getByText("MBSRN Operator Workspace")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign in to manage SEO operations" })).toBeInTheDocument();
    expect(screen.getByText("Manual Google ID token exchange (fallback)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mock Google Sign-In" })).toBeInTheDocument();
  });

  it("exchanges a manual id token and redirects to dashboard", async () => {
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Manual Google ID token exchange (fallback)"), {
      target: { value: "  token-123  " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Exchange Token" }));

    await waitFor(() => expect(mockExchangeGoogleIdToken).toHaveBeenCalledWith("token-123"));
    await waitFor(() => expect(mockSetSession).toHaveBeenCalled());
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });

  it("shows redirecting state when an authenticated principal is already present", async () => {
    mockUseAuth.mockReturnValue({
      setSession: mockSetSession,
      principal: {
        business_id: "biz-1",
        principal_id: "admin-1",
        display_name: "Admin One",
        role: "admin",
        is_active: true,
      },
    });

    render(<LoginPage />);

    expect(await screen.findByText("Finalizing your Operator Workspace session...")).toBeInTheDocument();
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });
});
