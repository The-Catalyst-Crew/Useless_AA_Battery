import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Image Persona Generator - AI-Powered Character Creation",
  description: "Upload photos and let AI create unique personalities and backstories for objects in your images. Powered by Z.ai and advanced computer vision.",
  keywords: ["AI persona generator", "image analysis", "character creation", "Z.ai", "computer vision", "creative AI"],
  authors: [{ name: "Z.ai Team" }],
  openGraph: {
    title: "Image Persona Generator",
    description: "Create unique personalities for objects in your photos using AI",
    url: "https://chat.z.ai",
    siteName: "Z.ai",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Image Persona Generator",
    description: "Create unique personalities for objects in your photos using AI",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
