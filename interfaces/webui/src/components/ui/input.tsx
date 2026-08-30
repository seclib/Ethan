"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  error?: string;
  success?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, iconRight, error, success, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary pointer-events-none">
            {icon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            "flex h-9 w-full rounded-[var(--radius-sm)] border bg-background px-3 py-2 text-sm text-foreground placeholder:text-foreground-tertiary transition-all duration-150 shadow-sm",
            "focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-accent-400 focus:shadow-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error
              ? "border-error-500"
              : success
              ? "border-success-500"
              : "border-line-2 hover:border-[var(--fg)] focus:border-accent-400",
            icon && "pl-10",
            iconRight && "pr-10",
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${props.id}-error` : undefined}
          ref={ref}
          {...props}
        />
        {iconRight && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-tertiary">
            {iconRight}
          </div>
        )}
        {error && (
          <p
            id={`${props.id}-error`}
            className="mt-1 text-xs text-error-600"
            role="alert"
          >
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };