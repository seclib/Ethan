"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-sm)] text-sm font-medium transition-all duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent-400 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // "default" is the primary action — aligns with Tailwind/shadcn convention
        default:
          "bg-accent-600 text-white shadow-sm hover:bg-accent-500 active:scale-[0.98]",
        // alias kept for backward compatibility with existing call-sites
        primary:
          "bg-accent-600 text-white shadow-sm hover:bg-accent-500 active:scale-[0.98]",
        secondary:
          "bg-background border border-line-2 text-foreground shadow-none hover:bg-surface hover:border-[var(--fg)] active:scale-[0.98]",
        outline:
          "border border-line-2 bg-background text-foreground shadow-none hover:bg-surface hover:border-[var(--fg)] active:scale-[0.98]",
        ghost:
          "text-foreground-secondary hover:bg-elevated hover:text-foreground",
        destructive:
          "bg-error-600 text-white shadow-sm hover:bg-error-500 active:scale-[0.98]",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ComponentProps<"button">,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  /** @deprecated Pass the icon as a direct child instead */
  icon?: React.ReactNode;
  /** @deprecated Pass the icon as a direct child instead */
  iconRight?: React.ReactNode;
}

function Button({
  className,
  variant,
  size,
  loading = false,
  icon,
  iconRight,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || loading}
      aria-busy={loading}
      aria-disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {!loading && icon && <span className="shrink-0">{icon}</span>}
      {children}
      {!loading && iconRight && <span className="shrink-0">{iconRight}</span>}
    </button>
  );
}

export { Button, buttonVariants };