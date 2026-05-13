import "./globals.css";

import Link from "next/link";
import type { Metadata, Route } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Finahunt 金融资讯认知系统",
  description: "公开市场资讯、题材发酵、低位研究与工作台总览。",
};

const navItems = [
  { href: "/", label: "首页" },
  { href: "/fermentation", label: "题材" },
  { href: "/research", label: "样例" },
  { href: "/workbench", label: "工作台" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="fi-top">
          <div className="fi-top-line" />
          <div className="fi-top-main fi-wrap">
            <Link className="fi-logo" href="/" aria-label="Finahunt 首页">
              <span className="fi-logo-mark">FH</span>
              <span className="fi-logo-text">金融资讯认知系统</span>
            </Link>
            <form className="fi-search" action="/workbench" method="get">
              <span aria-hidden="true">⌕</span>
              <input name="q" placeholder="搜索资讯、题材、公司、事件" />
              <button type="submit">搜索</button>
            </form>
            <Link className="fi-login" href="/sprint-2">验收</Link>
          </div>
          <nav className="fi-nav" aria-label="主导航">
            <div className="fi-wrap fi-nav-inner">
              {navItems.map((item) => <Link key={item.href} href={item.href as Route}>{item.label}</Link>)}
            </div>
          </nav>
        </header>
        {children}
        <footer className="fi-footer">
          <div className="fi-wrap">
            <span>关于我们</span><span>免责声明</span><span>隐私政策</span><span>联系方式</span>
            <span className="fi-footer-copy">© 2026 Finahunt，仅供研究观察，不构成投资建议</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
