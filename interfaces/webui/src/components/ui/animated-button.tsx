"use client";

import { type ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useAnimations";

interface AnimatedButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
}

export function AnimatedButton({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  className = "",
}: AnimatedButtonProps) {
  const reducedMotion = useReducedMotion();

  const baseClasses = "btn-lift";
  const variantClasses = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "btn-ghost",
  };

  const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";

  const animationStyle = reducedMotion
    ? {}
    : {
        transitionDuration: "150ms",
      };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${disabledClasses} ${className}`}
      onClick={onClick}
      disabled={disabled}
      style={animationStyle}
    >
      {children}
    </button>
  );
}