import "./globals.css";

import Link from "next/link";
import { Cormorant_Garamond, IBM_Plex_Mono, Manrope } from "next/font/google";
import type { Metadata } from "next";
import type { ReactNode } from "react";

const headingFont = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "600", "700"],
});

const bodyFont = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

const monoFont = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Finahunt 研究工作台",
  description: "按研究流程拆分的今日入口、主线发酵、低位研究与工作台总览。",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html className={`${headingFont.variable} ${bodyFont.variable} ${monoFont.variable}`} lang="zh-CN">
      <body>
        <div className="site-shell">
          <header className="masthead">
            <div className="masthead-note">
              <span>Finahunt Research Edition</span>
              <span>公开市场信号研究版 · 按研究流程而不是按功能堆叠页面</span>
            </div>

            <div className="masthead-bar">
              <Link className="brand-lockup" href="/">
                <span className="brand-mark">FH</span>
                <span className="brand-copy">
                  <strong>Finahunt</strong>
                  <small>研究工作台 · Editorial Research Edition</small>
                </span>
              </Link>

              <nav className="main-nav" aria-label="主导航">
                <Link href="/">今日入口</Link>
                <Link href="/fermentation">主线发酵</Link>
                <Link href="/research">低位研究</Link>
                <Link href="/workbench">工作台总览</Link>
              </nav>
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
