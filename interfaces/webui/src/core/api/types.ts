export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  services: Record<string, "up" | "down">;
  timestamp: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  uptime: number;
}