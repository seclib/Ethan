import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with clsx and tailwind-merge
 * Usage: cn("base-class", condition && "conditional-class", { "variant-class": true })
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  if (days < 7) return `${days} day${days > 1 ? "s" : ""} ago`;
  return date.toLocaleDateString();
}

/**
 * Format time to HH:MM:SS from total seconds
 * Use formatDuration for milliseconds or formatRelativeTime for dates
 */
export function formatTime(seconds: number | string): string {
  const num = typeof seconds === "string" ? parseFloat(seconds) : seconds;
  const h = Math.floor(num / 3600);
  const m = Math.floor((num % 3600) / 60);
  const s = Math.floor(num % 60);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

/**
 * Format duration in milliseconds to human readable string
 */
export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (seconds < 60) return `${seconds}s`;
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  return `${hours}h ${minutes % 60}m`;
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(7)}`;
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Format number with locale
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat("en-US").format(num);
}

/**
 * Format bytes to human readable
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Get status color as Badge variant
 */
export function getStatusColor(status: string): "default" | "success" | "warning" | "error" | "info" | "dim" {
  const map: Record<string, "default" | "success" | "warning" | "error" | "info" | "dim"> = {
    idle: "default",
    running: "success",
    paused: "warning",
    error: "error",
    stopped: "dim",
    pending: "default",
    active: "info",
    completed: "success",
    failed: "error",
    cancelled: "dim",
    skipped: "dim",
    planning: "info",
    waiting_approval: "warning",
    candidate: "info",
    stale: "warning",
    archived: "dim",
    superseded: "default",
    conflicted: "error",
    needs_review: "warning",
  };

  return map[status] || "default";
}


/**
 * Get priority color
 */
export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    low: "text-gray-400",
    medium: "text-blue-400",
    high: "text-yellow-400",
    critical: "text-red-400",
  };

  return colors[priority] || "text-gray-400";
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}


/**
 * Format access level to string
 */
export function formatAccessLevel(level: number): string {
  const levels = [
    "Read Only",
    "Write Local",
    "Execute Code",
    "Network",
    "Install Package",
    "Modify Core",
  ];
  return levels[level] || `Level ${level}`;
}

/**
 * Format autonomy level to string
 */
export function formatAutonomyLevel(level: number): string {
  const levels = [
    "Respond Only",
    "Suggest",
    "Prepare Draft",
    "Execute in Sandbox",
    "Modify Project Files",
    "Publish/Pay/Contact",
  ];
  return levels[level] || `Level ${level}`;
}