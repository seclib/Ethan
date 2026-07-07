"use client";

import { type ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useAnimations";

interface AnimatedCardProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  onClick?: () => void;
}

export function AnimatedCard({
  children,
  className = "",
  delay = 0,
  onClick,
}: AnimatedCardProps) {
  const reducedMotion = useReducedMotion();

  const baseClasses = "card-glow";
  const animationClass = reducedMotion ? "" : "widget-appear";
  const clickableClasses = onClick ? "cursor-pointer" : "";

  const style = reducedMotion
    ? {}
    : {
        animationDelay: `${delay}ms`,
      };

  return (
    <div
      className={`${baseClasses} ${animationClass} ${clickableClasses} ${className}`}
      style={style}
      onClick={onClick}
    >
      {children}
    </div>
  );
}