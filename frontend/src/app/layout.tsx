import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VibeMotion AI | Short-Form AI Video Generator Studio",
  description:
    "Generate short AI videos from text prompts and reference images for TikTok, Instagram Reels, and YouTube Shorts.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090A0F] text-slate-100 antialiased selection:bg-purple-500/30 selection:text-purple-200">
        {children}
      </body>
    </html>
  );
}
