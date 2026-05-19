import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinAlly — AI Trading Workstation",
  description:
    "FinAlly is an AI-powered trading workstation with live market data, a simulated portfolio, and an integrated LLM copilot.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface-0 text-text-primary min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
