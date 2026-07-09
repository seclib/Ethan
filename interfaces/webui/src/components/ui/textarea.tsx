"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  success?: boolean;
  resizable?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, success, resizable = true, ...props }, ref) => {
    return (
      <div className="relative w-full">
        <textarea
          className={cn(
            "flex min-h-[80px] w-full rounded-lg border bg-background px-3 py-2 text-sm text-foreground placeholder:text-foreground-tertiary transition-all duration-100",
            "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-400",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error
              ? "border-error-500 focus:ring-error-500"
              : success
              ? "border-success-500 focus:ring-success-500"
              : "border-line-2 hover:border-line-3 focus:border-accent-400",
            !resizable && "resize-none",
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${props.id}-error` : undefined}
          ref={ref}
          {...props}
        />
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
Textarea.displayName = "Textarea";

export { Textarea };