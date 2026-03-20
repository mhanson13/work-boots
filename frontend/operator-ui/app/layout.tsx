import "./globals.css";
import type { Metadata } from "next";
import { AuthProvider } from "../components/AuthProvider";
import { NavShell } from "../components/NavShell";

export const metadata: Metadata = {
  title: "mbsrn Operator Console",
  description: "Operator UI for mbsrn",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <NavShell>{children}</NavShell>
        </AuthProvider>
      </body>
    </html>
  );
}
