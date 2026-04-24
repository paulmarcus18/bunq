import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinPilot Inbox",
  description: "AI financial triage assistant for bunq hackathon demos.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
