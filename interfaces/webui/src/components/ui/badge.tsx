"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors duration-100",
  {
    variants: {
      variant: {
        default: "bg-elevated text-foreground-secondary",
        primary: "bg-accent-600/10 text-accent-600",
        success: "bg-success-500/10 text-success-600",
        warning: "bg-warning-500/10 text-warning-600",
        error: "bg-error-500/10 text-error-600",
        info: "bg-info-500/10 text-info-600",
        dim: "bg-line-1 text-foreground-tertiary",
      },
      size: {
        sm: "px-2 py-0 text-[10px]",
        md: "px-2.5 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
      dot: {
        true: "before:inline-block before:w-1.5 before:h-1.5 before:rounded-full before:bg-current",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface BadgeProps
  extends React.ComponentProps<"span">,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

function Badge({ className, variant, size, dot, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(badgeVariants({ variant, size, dot, className }))}
      role="status"
      {...props}
    >
      {children}
    </span>
  );
}

export { Badge, badgeVariants };