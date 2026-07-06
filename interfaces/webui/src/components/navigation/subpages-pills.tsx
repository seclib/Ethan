"use client";

interface Subpage {
  id: string;
  label: string;
  icon?: string;
}

interface SubpagesPillsProps {
  pages: Subpage[];
  active: string;
  onChange: (id: string) => void;
}

export function SubpagesPills({ pages, active, onChange }: SubpagesPillsProps) {
  if (!pages.length) return null;
  return (
    <nav className="subpages-pills" role="tablist">
      {pages.map((p) => (
        <button
          key={p.id}
          role="tab"
          aria-selected={active === p.id}
          data-active={active === p.id}
          onClick={() => onChange(p.id)}
        >
          {p.icon && <span className="subpages-icon">{p.icon}</span>}
          {p.label}
        </button>
      ))}
    </nav>
  );
}