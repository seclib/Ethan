"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

interface CommandItem {
  id: string;
  label: string;
  category?: string;
  icon?: React.ReactNode;
  shortcut?: string;
  onSelect: () => void;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  items: CommandItem[];
  recent?: CommandItem[];
  placeholder?: string;
}

function fuzzySearch(query: string, text: string): boolean {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  let qi = 0;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (q[qi] === t[ti]) qi++;
  }
  return qi === q.length;
}

function CommandPalette({
  open,
  onClose,
  items,
  recent = [],
  placeholder = "Search commands...",
}: CommandPaletteProps) {
  const [query, setQuery] = React.useState("");
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLDivElement>(null);

  // Filter items by query
  const filtered = React.useMemo(() => {
    if (!query.trim()) return items;
    return items.filter((item) => fuzzySearch(query, item.label));
  }, [query, items]);

  // Reset on open/close
  React.useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filtered.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
        break;
      case "Enter":
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].onSelect();
          onClose();
        }
        break;
      case "Escape":
        e.preventDefault();
        onClose();
        break;
    }
  };

  // Scroll selected item into view
  React.useEffect(() => {
    if (listRef.current) {
      const selected = listRef.current.querySelector<HTMLButtonElement>(
        `[data-index="${selectedIndex}"]`
      );
      selected?.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  if (!open) return null;

  // Group items by category
  const grouped = filtered.reduce<Record<string, CommandItem[]>>((acc, item) => {
    const cat = item.category || "General";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  return (
    <div
      className="fixed inset-0 z-modal flex items-start justify-center pt-[15vh]"
      role="dialog"
      aria-label="Command palette"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={cn(
          "relative w-full max-w-lg mx-4 rounded-xl border border-line-2 bg-background shadow-xl overflow-hidden",
          "animate-in fade-in zoom-in-95 duration-150"
        )}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-line-1">
          <Search className="w-4 h-4 text-foreground-tertiary shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-foreground-tertiary outline-none"
            aria-label="Search commands"
          />
          <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium text-foreground-tertiary bg-elevated rounded">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div
          ref={listRef}
          className="max-h-[300px] overflow-y-auto p-2"
          role="listbox"
        >
          {/* Recent section */}
          {!query.trim() && recent.length > 0 && (
            <div className="mb-2">
              <p className="px-2 py-1 text-[10px] font-semibold text-foreground-tertiary uppercase tracking-wider">
                Recent
              </p>
              {recent.map((item) => (
                <button
                  key={item.id}
                  role="option"
                  aria-selected={false}
                  data-index={-1}
                  onClick={() => {
                    item.onSelect();
                    onClose();
                  }}
                  className="flex items-center gap-3 w-full px-2 py-2 text-sm rounded-md text-foreground-secondary hover:bg-elevated hover:text-foreground transition-colors duration-100"
                >
                  {item.icon && <span className="w-4 h-4 shrink-0">{item.icon}</span>}
                  <span className="flex-1 text-left">{item.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* Filtered results */}
          {Object.entries(grouped).map(([category, categoryItems]) => (
            <div key={category} className="mb-2 last:mb-0">
              <p className="px-2 py-1 text-[10px] font-semibold text-foreground-tertiary uppercase tracking-wider">
                {category}
              </p>
              {categoryItems.map((item, idx) => {
                const globalIndex = filtered.indexOf(item);
                const isSelected = globalIndex === selectedIndex;

                return (
                  <button
                    key={item.id}
                    role="option"
                    aria-selected={isSelected}
                    data-index={globalIndex}
                    ref={(el) => {
                      if (isSelected && el) {
                        el.scrollIntoView({ block: "nearest" });
                      }
                    }}
                    onClick={() => {
                      item.onSelect();
                      onClose();
                    }}
                    className={cn(
                      "flex items-center gap-3 w-full px-2 py-2 text-sm rounded-md transition-colors duration-100",
                      isSelected
                        ? "bg-accent-600/10 text-accent-600"
                        : "text-foreground-secondary hover:bg-elevated hover:text-foreground"
                    )}
                  >
                    {item.icon && <span className="w-4 h-4 shrink-0">{item.icon}</span>}
                    <span className="flex-1 text-left">{item.label}</span>
                    {item.shortcut && (
                      <kbd className="text-[10px] text-foreground-tertiary bg-elevated px-1.5 py-0.5 rounded">
                        {item.shortcut}
                      </kbd>
                    )}
                  </button>
                );
              })}
            </div>
          ))}

          {filtered.length === 0 && (
            <p className="px-2 py-4 text-sm text-foreground-tertiary text-center">
              No results for "{query}"
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export { CommandPalette };
export type { CommandItem, CommandPaletteProps };