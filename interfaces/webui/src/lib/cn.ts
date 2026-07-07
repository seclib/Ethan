import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with clsx and tailwind-merge.
 * Usage: cn("base-class", condition && "conditional-class", { "variant-class": true })
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}