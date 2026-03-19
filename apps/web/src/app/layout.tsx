import "./globals.css";

import Link from "next/link";
import { IBM_Plex_Mono, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import type { Metadata } from "next";
import type { ReactNode } from "react";

const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "700"],
});

const bodyFont = IBM_Plex_Sans({
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
  description: "将公开市场信号整理成主线发酵、低位研究、证据回看和风险边界的一体化研究入口。",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html className={`${headingFont.variable} ${bodyFont.variable} ${monoFont.variable}`} lang="zh-CN">
      <body>
        <div className="site-shell">
          <div className="top-strip">
            <span>Finahunt 把公开信号压缩成“今日入口 + Sprint 2 研究工作台”的连续研究流程。</span>
            <Link href="/sprint-2">打开 Sprint 2 工作台</Link>
          </div>

          <header className="site-header">
            <Link className="brand-lockup" href="/">
              <span className="brand-mark">FH</span>
              <span>
                <strong>Finahunt</strong>
                <small>公开市场信号研究工作台</small>
              </span>
            </Link>

            <nav className="site-nav">
              <Link href="/">今日入口</Link>
              <Link href="/sprint-2">Sprint 2 工作台</Link>
              <Link href="/sprint-2?focus=fermentation&reason=compare">主线发酵</Link>
              <Link href="/sprint-2?focus=research&reason=compare">低位研究</Link>
            </nav>

            <div className="header-actions">
              <Link className="ghost-link" href="/">
                查看日报
              </Link>
              <Link className="header-pill" href="/sprint-2">
                进入工作台
              </Link>
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
