"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";

const SECTIONS = [
  { id: "dashboard", label: "DASH", href: "/", chapter: "I" },
  { id: "flux", label: "FLUX", href: "/flux", chapter: "II" },
  { id: "agents", label: "AGENTS", href: "/agents", chapter: "III" },
  { id: "memory", label: "MÉMOIRE", href: "/memory", chapter: "IV" },
  { id: "skills", label: "SKILLS", href: "/skills", chapter: "V" },
  { id: "config", label: "CONF", href: "/config", chapter: "VI" },
];

export function TopNav() {
  const pathname = usePathname();

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        {SECTIONS.map((s) => {
          const active = pathname === s.href || (s.href !== "/" && pathname.startsWith(s.href));
          return (
            <Link
              key={s.id}
              href={s.href}
              className="top-nav-link"
              data-active={active}
            >
              <span className="top-nav-chapter">{s.chapter}</span>
              <span className="top-nav-label">{s.label}</span>
            </Link>
          );
        })}
      </div>
    </header>
  );
}