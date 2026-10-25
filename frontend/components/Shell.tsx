"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

const links = [
  { href: "/", label: "Overview" },
  { href: "/transactions", label: "Transactions" },
  { href: "/alerts", label: "Alerts" },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link className="brand" href="/" onClick={() => setMenuOpen(false)}>
          <span className="brand-mark" aria-hidden="true"><i /><b /></span>
          <span><strong>Onchain</strong><small>Risk investigations</small></span>
        </Link>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="primary-nav" aria-label="Main navigation">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return <Link key={link.href} href={link.href} className={active ? "nav-link active" : "nav-link"} aria-current={active ? "page" : undefined} onClick={() => setMenuOpen(false)}>{link.label}</Link>;
          })}
        </nav>
        <div className="sidebar-foot"><span className="connection-dot" /> Local workspace</div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <button className="mobile-menu" type="button" aria-label="Toggle navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}><span /><span /><span /></button>
          <div className="topbar-context"><span className="context-mark" /> Onchain monitor <span className="context-divider">/</span> Analyst workspace</div>
          <span className="api-indicator">API target · local</span>
        </header>
        <main className="sheet">{children}</main>
        <footer className="app-footer"><span>Risk indicators support review; they do not establish fraud.</span><span>Evidence first · AI as an investigative aid</span></footer>
      </div>
    </div>
  );
}
