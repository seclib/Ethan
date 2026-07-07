"use client";

import { CpuCard } from "./cards/cpu-card";
import { RamCard } from "./cards/ram-card";
import { GpuCard } from "./cards/gpu-card";
import { ProvidersCard } from "./cards/providers-card";
import { TokensCard } from "./cards/tokens-card";
import { AgentsCard } from "./cards/agents-card";
import { PlannerCard } from "./cards/planner-card";
import { KnowledgeCard } from "./cards/knowledge-card";
import { MemoryCard } from "./cards/memory-card";
import { McpCard } from "./cards/mcp-card";
import { PluginsCard } from "./cards/plugins-card";
import { CoreCard } from "./cards/core-card";
import { EventsCard } from "./cards/events-card";
import { NetworkCard } from "./cards/network-card";

// Mock data generators
const generateCpuData = () => ({
  usage: Math.floor(Math.random() * 60) + 20,
  cores: 8,
  frequency: 3200,
  temperature: Math.floor(Math.random() * 30) + 50,
  load1: Math.random() * 2,
  load5: Math.random() * 2,
  load15: Math.random() * 2,
});

const generateRamData = () => ({
  used: Math.floor(Math.random() * 8) + 4,
  total: 16,
  available: Math.floor(Math.random() * 4) + 2,
  cached: Math.floor(Math.random() * 2) + 1,
  swapUsed: Math.floor(Math.random() * 2),
  swapTotal: 4,
});

const generateGpuData = () => ({
  name: "NVIDIA RTX 4090",
  utilization: Math.floor(Math.random() * 50) + 30,
  vramUsed: Math.floor(Math.random() * 10) + 12,
  vramTotal: 24,
  temperature: Math.floor(Math.random() * 20) + 55,
  power: Math.floor(Math.random() * 100) + 250,
  frequency: Math.floor(Math.random() * 500) + 2000,
});

const generateProvidersData = () => [
  { name: "Ollama", connected: true, latencyMs: Math.floor(Math.random() * 5) + 1 },
  { name: "OpenAI", connected: Math.random() > 0.2, latencyMs: Math.floor(Math.random() * 200) + 150 },
  { name: "OpenRouter", connected: Math.random() > 0.5, latencyMs: Math.floor(Math.random() * 300) + 200 },
  { name: "Anthropic", connected: Math.random() > 0.7, latencyMs: Math.floor(Math.random() * 250) + 180 },
];

const generateTokensData = () => ({
  used: Math.floor(Math.random() * 4000) + 2000,
  total: 8192,
  rate: Math.floor(Math.random() * 50) + 10,
  cost: Math.random() * 0.5,
  model: "gemma3:4b",
});

const generateAgentsData = () => [
  { name: "planner", status: "run" as const },
  { name: "executor", status: "run" as const },
  { name: "memory", status: "idle" as const },
  { name: "learning", status: "sleep" as const },
  { name: "reflective", status: "sleep" as const },
  { name: "autonomy", status: "sleep" as const },
];

const generatePlannerData = () => ({
  objective: "Optimiser pipeline RAG",
  tasksDone: Math.floor(Math.random() * 5) + 1,
  tasksTotal: 8,
  nextStep: "embed.chunk → memory.store",
});

const generateKnowledgeData = () => ({
  entries: Math.floor(Math.random() * 500) + 2000,
  skills: Math.floor(Math.random() * 10) + 15,
  contextUsed: Math.floor(Math.random() * 3000) + 2000,
  contextTotal: 8192,
  embeddings: Math.floor(Math.random() * 1000) + 1500,
});

const generateMemoryData = () => ({
  entries: Math.floor(Math.random() * 500) + 2000,
  redisKeys: Math.floor(Math.random() * 100) + 200,
  postgresEvents: Math.floor(Math.random() * 10000) + 50000,
  sizeMb: Math.floor(Math.random() * 500) + 200,
  hitRate: Math.floor(Math.random() * 10) + 88,
});

const generateMcpData = () => ({
  toolsAvailable: 24,
  toolsCalled: Math.floor(Math.random() * 100) + 50,
  successRate: Math.floor(Math.random() * 5) + 94,
  avgLatency: Math.floor(Math.random() * 50) + 20,
  errors: Math.floor(Math.random() * 3),
});

const generatePluginsData = () => [
  { name: "security", active: true, version: "1.2.0" },
  { name: "browser", active: true, version: "2.0.1" },
  { name: "twitter", active: Math.random() > 0.3, version: "1.5.0" },
  { name: "slack", active: true, version: "1.1.0" },
  { name: "docker", active: true, version: "3.0.0" },
  { name: "github", active: Math.random() > 0.5, version: "1.0.0" },
  { name: "notion", active: false, version: "0.9.0" },
  { name: "telegram", active: true, version: "1.3.0" },
];

const generateCoreData = () => ({
  status: "online" as const,
  uptime: "14h 22m",
  version: "2.4.1",
  pid: 12847,
});

const generateEventsData = () => ({
  total: Math.floor(Math.random() * 10000) + 50000,
  rate: Math.floor(Math.random() * 10) + 5,
  errors: Math.floor(Math.random() * 5),
  warnings: Math.floor(Math.random() * 10),
});

const generateNetworkData = () => ({
  latency: Math.floor(Math.random() * 50) + 10,
  bandwidth: Math.floor(Math.random() * 500) + 800,
  packetsIn: Math.floor(Math.random() * 1000) + 5000,
  packetsOut: Math.floor(Math.random() * 1000) + 3000,
  errors: Math.floor(Math.random() * 3),
});

export function DashboardGrid() {
  return (
    <div className="db-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
      <CoreCard data={generateCoreData()} />
      <CpuCard data={generateCpuData()} />
      <RamCard data={generateRamData()} />
      <GpuCard data={generateGpuData()} />
      <ProvidersCard data={generateProvidersData()} />
      <TokensCard data={generateTokensData()} />
      <AgentsCard data={generateAgentsData()} />
      <PlannerCard data={generatePlannerData()} />
      <KnowledgeCard data={generateKnowledgeData()} />
      <MemoryCard data={generateMemoryData()} />
      <McpCard data={generateMcpData()} />
      <PluginsCard data={generatePluginsData()} />
      <EventsCard data={generateEventsData()} />
      <NetworkCard data={generateNetworkData()} />
    </div>
  );
}