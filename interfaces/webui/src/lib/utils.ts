import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function truncate(str: string, len = 40): string {
  if (str.length <= len) return str;
  return str.slice(0, len) + "…";
}

export function shortId(id: string, chars = 8): string {
  return id.length > chars ? id.slice(0, chars) : id;
}

export function statusColor(
  status: string
): "success" | "warning" | "error" | "info" | "dim" {
  switch (status) {
    case "active":
    case "running":
    case "online":
    case "ok":
    case "passed":
      return "success";
    case "pending":
    case "idle":
      return "info";
    case "warning":
    case "degraded":
      return "warning";
    case "error":
    case "failed":
    case "offline":
    case "cancelled":
      return "error";
    default:
      return "dim";
  }
}