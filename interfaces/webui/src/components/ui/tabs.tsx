"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface Tab {
  value: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  content?: React.ReactNode;
}

interface TabsProps {
  variant?: "line" | "pill";
  size?: "sm" | "md" | "lg";
  items: Tab[];
  defaultValue?: string;
  value?: string;
  onChange?: (value: string) => void;
  className?: string;
}

function Tabs({
  variant = "line",
  size = "md",
  items,
  defaultValue,
  value: controlledValue,
  onChange,
  className,
}: TabsProps) {
  const [internalValue, setInternalValue] = React.useState(defaultValue || items[0]?.value || "");
  const value = controlledValue ?? internalValue;

  const handleChange = (tabValue: string) => {
    if (tabValue === value) return;
    setInternalValue(tabValue);
    onChange?.(tabValue);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    const enabledItems = items.filter((item) => !item.disabled);
    const currentIndex = enabledItems.findIndex((item) => item.value === value);

    let nextIndex: number | null = null;

    switch (e.key) {
      case "ArrowRight":
        e.preventDefault();
        nextIndex = (currentIndex + 1) % enabledItems.length;
        break;
      case "ArrowLeft":
        e.preventDefault();
        nextIndex = (currentIndex - 1 + enabledItems.length) % enabledItems.length;
        break;
      case "Home":
        e.preventDefault();
        nextIndex = 0;
        break;
      case "End":
        e.preventDefault();
        nextIndex = enabledItems.length - 1;
        break;
    }

    if (nextIndex !== null) {
      const nextTab = enabledItems[nextIndex];
      handleChange(nextTab.value);
      // Focus the next tab button
      const buttons = document.querySelectorAll('[role="tab"]');
      (buttons[nextIndex] as HTMLButtonElement)?.focus();
    }
  };

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  const activeClasses = (isActive: boolean, disabled?: boolean) => {
    if (disabled) return "text-foreground-disabled cursor-not-allowed";
    if (variant === "line") {
      return isActive
        ? "text-accent-500 border-b-2 border-accent-500"
        : "text-foreground-secondary hover:text-foreground border-b-2 border-transparent";
    }
    return isActive
      ? "bg-accent-600 text-white"
      : "text-foreground-secondary hover:text-foreground hover:bg-elevated";
  };

  const activeTab = items.find((item) => item.value === value);

  return (
    <div className={className}>
      {/* Tab list */}
      <div
        className={cn(
          "flex",
          variant === "pill" && "gap-1 p-1 bg-elevated rounded-lg",
          variant === "line" && "border-b border-line-1"
        )}
        role="tablist"
        aria-orientation="horizontal"
      >
        {items.map((tab, index) => {
          const isActive = tab.value === value;
          return (
            <button
              key={tab.value}
              role="tab"
              id={`tab-${tab.value}`}
              aria-selected={isActive}
              aria-controls={`tabpanel-${tab.value}`}
              aria-disabled={tab.disabled}
              tabIndex={isActive ? 0 : -1}
              disabled={tab.disabled}
              onClick={() => handleChange(tab.value)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className={cn(
                "inline-flex items-center gap-2 px-3 py-2 font-medium transition-all duration-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400 focus-visible:ring-offset-2",
                sizeClasses[size],
                activeClasses(isActive, tab.disabled),
                variant === "pill" && "rounded-md",
                variant === "line" && "mb-[-1px]"
              )}
            >
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab panel */}
      {activeTab?.content && (
        <div
          role="tabpanel"
          id={`tabpanel-${activeTab.value}`}
          aria-labelledby={`tab-${activeTab.value}`}
          className="mt-4 focus-visible:outline-none"
          tabIndex={0}
        >
          {activeTab.content}
        </div>
      )}
    </div>
  );
}

export { Tabs };
export type { Tab, TabsProps };