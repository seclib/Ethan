"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Check, ChevronRight } from "lucide-react";

interface DropdownItem {
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  checked?: boolean;
  onClick?: () => void;
  items?: DropdownItem[];
}

interface DropdownMenuProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: "start" | "end";
  side?: "top" | "bottom";
  className?: string;
}

function DropdownMenu({ trigger, items, align = "start", side = "bottom", className }: DropdownMenuProps) {
  const [open, setOpen] = React.useState(false);
  const [focusIndex, setFocusIndex] = React.useState(-1);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const triggerRef = React.useRef<HTMLDivElement>(null);

  // Close on click outside
  React.useEffect(() => {
    if (!open) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node) &&
          triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.querySelector("button")?.focus();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  // Focus first item when opening
  React.useEffect(() => {
    if (open) {
      setFocusIndex(0);
    } else {
      setFocusIndex(-1);
    }
  }, [open]);

  // Focus management
  React.useEffect(() => {
    if (focusIndex >= 0 && menuRef.current) {
      const buttons = menuRef.current.querySelectorAll<HTMLButtonElement>('[role="menuitem"]:not([aria-disabled="true"])');
      buttons[focusIndex]?.focus();
    }
  }, [focusIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const enabledItems = items.filter((item) => !item.disabled);

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setFocusIndex((prev) => (prev + 1) % enabledItems.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setFocusIndex((prev) => (prev - 1 + enabledItems.length) % enabledItems.length);
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        if (focusIndex >= 0 && enabledItems[focusIndex]) {
          enabledItems[focusIndex].onClick?.();
          setOpen(false);
        }
        break;
    }
  };

  const handleItemClick = (item: DropdownItem) => {
    if (item.disabled) return;
    item.onClick?.();
    setOpen(false);
  };

  const renderItem = (item: DropdownItem, index: number) => {
    if (item.label === "separator") {
      return <div key={`sep-${index}`} className="h-px bg-line-1 my-1" role="separator" />;
    }

    return (
      <button
        key={item.label}
        role="menuitem"
        aria-disabled={item.disabled}
        disabled={item.disabled}
        onClick={() => handleItemClick(item)}
        className={cn(
          "flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md transition-colors duration-100",
          "focus-visible:outline-none focus-visible:bg-elevated",
          item.danger
            ? "text-error-600 hover:bg-error-50 data-[theme=dark]:hover:bg-error-600/10"
            : "text-foreground hover:bg-elevated",
          item.disabled && "text-foreground-disabled cursor-not-allowed hover:bg-transparent"
        )}
      >
        {item.icon && <span className="shrink-0 w-4 h-4">{item.icon}</span>}
        {!item.icon && item.checked !== undefined && (
          <span className="shrink-0 w-4 h-4">
            {item.checked && <Check className="w-4 h-4" />}
          </span>
        )}
        <span className="flex-1 text-left">{item.label}</span>
        {item.shortcut && (
          <span className="text-xs text-foreground-tertiary">{item.shortcut}</span>
        )}
        {item.items && <ChevronRight className="w-3.5 h-3.5 text-foreground-tertiary" />}
      </button>
    );
  };

  return (
    <div className={cn("relative inline-block", className)} ref={triggerRef}>
      {/* Trigger */}
      <div
        onClick={() => setOpen(!open)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen(!open);
          }
        }}
        role="button"
        tabIndex={0}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {trigger}
      </div>

      {/* Menu */}
      {open && (
        <div
          ref={menuRef}
          role="menu"
          aria-orientation="vertical"
          onKeyDown={handleKeyDown}
          className={cn(
            "absolute z-dropdown min-w-[200px] p-1.5 rounded-lg border border-line-2 bg-background shadow-xl",
            "animate-in fade-in zoom-in-95 duration-100",
            side === "bottom" ? "mt-1" : "mb-1 bottom-full",
            align === "end" ? "right-0" : "left-0"
          )}
        >
          {items.map((item, index) => renderItem(item, index))}
        </div>
      )}
    </div>
  );
}

export { DropdownMenu };
export type { DropdownItem, DropdownMenuProps };