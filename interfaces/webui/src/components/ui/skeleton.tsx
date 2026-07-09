"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.ComponentProps<"div"> {
  variant?: "text" | "circle" | "rectangle";
  lines?: number;
}

function Skeleton({ className, variant = "text", lines = 1, ...props }: SkeletonProps) {
  if (variant === "text") {
    return (
      <div className="flex flex-col gap-2" {...props}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-4 rounded-md bg-line-1 animate-shimmer",
              i === lines - 1 && lines > 1 && "w-3/4",
              className
            )}
            style={{
              background: "linear-gradient(90deg, var(--line-1) 25%, var(--line-2) 50%, var(--line-1) 75%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.5s infinite",
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === "circle") {
    return (
      <div
        className={cn("rounded-full bg-line-1 animate-shimmer", className)}
        style={{
          background: "linear-gradient(90deg, var(--line-1) 25%, var(--line-2) 50%, var(--line-1) 75%)",
          backgroundSize: "200% 100%",
          animation: "shimmer 1.5s infinite",
        }}
        {...props}
      />
    );
  }

  return (
    <div
      className={cn("rounded-lg bg-line-1 animate-shimmer", className)}
      style={{
        background: "linear-gradient(90deg, var(--line-1) 25%, var(--line-2) 50%, var(--line-1) 75%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s infinite",
      }}
      {...props}
    />
  );
}

export { Skeleton };