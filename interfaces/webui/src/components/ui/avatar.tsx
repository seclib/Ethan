"use client";

import * as React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface AvatarProps extends React.ComponentProps<"div"> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

const sizeClasses = {
  sm: "w-6 h-6 text-[10px]",
  md: "w-8 h-8 text-xs",
  lg: "w-12 h-12 text-sm",
  xl: "w-16 h-16 text-base",
};

function getInitials(fallback?: string): string {
  if (!fallback) return "?";
  return fallback
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function Avatar({ className, src, alt = "", fallback, size = "md", ...props }: AvatarProps) {
  const [imgError, setImgError] = React.useState(false);

  const showImage = src && !imgError;

  return (
    <div
      className={cn(
        "relative inline-flex items-center justify-center rounded-full bg-elevated text-foreground-secondary font-medium overflow-hidden shrink-0",
        sizeClasses[size],
        className
      )}
      role="img"
      aria-label={alt || fallback || "Avatar"}
      {...props}
    >
      {showImage ? (
        <Image
          src={src!}
          alt={alt || fallback || ""}
          fill
          sizes="100%"
          className="object-cover"
          onError={() => setImgError(true)}
        />
      ) : (
        <span className="select-none">{getInitials(fallback)}</span>
      )}
    </div>
  );
}

export { Avatar };