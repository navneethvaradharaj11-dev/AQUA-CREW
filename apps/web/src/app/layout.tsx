import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ThemeProvider } from "@/context/ThemeContext";

export const metadata: Metadata = {
  title: "AQUA CREW — Autonomous Water Leakage Detection & Fleet Management",
  description:
    "Metropolitan autonomous water leakage detection, pipeline localization, and repair management platform.",
  applicationName: "AQUA CREW",
  keywords: [
    "water leakage detection",
    "autonomous rovers",
    "metropolitan pipeline",
    "acoustic sensing",
    "smart utility management",
    "robotics",
  ],
  authors: [{ name: "AQUA CREW Engineering Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#02060e",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <meta name="color-scheme" content="dark light" />
      </head>
      <body className="min-h-dvh bg-background text-foreground antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
