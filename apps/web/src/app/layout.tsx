import "./globals.css";

import Link from "next/link";
import type { Metadata, Route } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Finahunt 金融资讯认知系统",
  description: "公开市场事件认知、题材发酵、低位研究和证据工作台。",
};

const navItems = [
  { href: "/", label: "首页" },
  { href: "/workbench", label: "资讯" },
  { href: "/fermentation", label: "题材" },
  { href: "/research", label: "样例" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
          <defs>
            <symbol id="i-logo" viewBox="0 0 24 24"><path d="M12 2 21 7v10l-9 5-9-5V7l9-5Zm0 3.1L6 8.4v7.2l6 3.3 6-3.3V8.4l-6-3.3Z" /></symbol>
            <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="m20 20-4.2-4.2" /></symbol>
            <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 21c1.7-4 4.4-6 8-6s6.3 2 8 6" /></symbol>
            <symbol id="i-news" viewBox="0 0 24 24"><rect x="5" y="4" width="14" height="16" rx="2" /><path d="M8 8h8M8 12h8M8 16h5" /></symbol>
            <symbol id="i-flame" viewBox="0 0 24 24"><path d="M12 22c4 0 7-2.7 7-6.6 0-2.8-1.4-5.1-4-6.9.1 2.3-.8 3.6-2.4 4.4.5-3.1-.9-5.9-4.1-8.8C9 7.2 7 9.4 5.7 11.3 4.6 13 4 14.3 4 16c0 3.4 3 6 8 6Z" /></symbol>
            <symbol id="i-tags" viewBox="0 0 24 24"><path d="M20 10 13 3H5v8l7 7a2 2 0 0 0 2.8 0l5.2-5.2a2 2 0 0 0 0-2.8Z" /><circle cx="8.5" cy="6.5" r="1.2" /></symbol>
            <symbol id="i-activity" viewBox="0 0 24 24"><path d="M3 12h4l2-6 4 12 2-6h6" /></symbol>
            <symbol id="i-robot" viewBox="0 0 24 24"><rect x="6" y="8" width="12" height="10" rx="3" /><path d="M12 8V5M9 5h6M9 13h.01M15 13h.01M10 17h4" /></symbol>
            <symbol id="i-cpu" viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="2" /><path d="M4 9h3M4 15h3M17 9h3M17 15h3M9 4v3M15 4v3M9 17v3M15 17v3" /></symbol>
            <symbol id="i-plane" viewBox="0 0 24 24"><path d="M3 12 21 4l-5 16-4-7-9-1Zm9 1 4-4" /></symbol>
            <symbol id="i-battery" viewBox="0 0 24 24"><rect x="4" y="7" width="15" height="10" rx="2" /><path d="M21 11v2M11 9l-2 4h3l-2 4" /></symbol>
            <symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10Z" /></symbol>
            <symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></symbol>
          </defs>
        </svg>
        <header>
          <div className="top-line" />
          <div className="top-main">
            <div className="wrap">
              <Link className="logo" href="/" aria-label="Finahunt home">
                <span className="logo-mark"><Icon name="logo" size={25} /></span>
                <span className="logo-text">金融资讯认知系统</span>
              </Link>
              <form className="searchbar" action="/workbench" method="get">
                <Icon name="search" size={19} />
                <input name="q" placeholder="搜索资讯、题材、公司、事件等" />
                <button className="searchbtn" type="submit">搜索</button>
              </form>
              <Link className="login-btn" href="/workbench">
                <Icon name="user" size={18} /> 登录
              </Link>
            </div>
          </div>
          <nav className="nav" aria-label="main navigation">
            <div className="nav-inner wrap">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href as Route}>{item.label}</Link>
              ))}
            </div>
          </nav>
        </header>
        {children}
        <footer className="footer">
          <div className="wrap">
            <div className="footer-links">
              <span>关于我们</span>
              <span>免责声明</span>
              <span>隐私政策</span>
              <span>联系我们</span>
            </div>
            <div>© 2026 金融资讯认知系统 版权所有</div>
            <div>仅供研究观察，不构成投资建议</div>
          </div>
        </footer>
      </body>
    </html>
  );
}

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <use href={`#i-${name}`} />
    </svg>
  );
}
