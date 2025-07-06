import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";
import { cn } from "@/lib/utils";

const fontSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const fontMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Deniom - 决策智能平台",
  description: "发现 GitHub 上的商业机会，基于 AI 的深度分析与市场洞察",
  keywords: ["GitHub", "商业机会", "AI分析", "市场洞察", "技术创业", "科幻", "未来主义"],
};

export const viewport: Viewport = {
  themeColor: "#0d0d1a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="dark">
      <body
        className={cn(
          "font-sans antialiased",
          fontSans.variable,
          fontMono.variable
        )}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
