"use client";

import { useCallback, useMemo } from "react";
import { DEFAULT_LAYOUT } from "@/hooks/useDashboardLayout";
import {
  DndContext,
  closestCenter,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useDashboardLayout } from "@/hooks/useDashboardLayout";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
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

// ───────── Card registry ─────────
interface CardComponentProps {
  data: any;
  loading?: boolean;
  sparkline?: number[];
}

const CARD_REGISTRY: Record<string, React.FC<CardComponentProps>> = {
  core: CoreCard,
  cpu: CpuCard,
  ram: RamCard,
  gpu: GpuCard,
  providers: ProvidersCard,
  tokens: TokensCard,
  agents: AgentsCard,
  planner: PlannerCard,
  knowledge: KnowledgeCard,
  memory: MemoryCard,
  mcp: McpCard,
  plugins: PluginsCard,
  events: EventsCard,
  network: NetworkCard,
};

// ───────── Mock data generators ─────────
const MOCK_DATA: Record<string, () => any> = {
  core: () => ({ status: "online" as const, uptime: "14h 22m", version: "2.4.1", pid: 12847 }),
  cpu: () => ({ usage: Math.floor(Math.random() * 60) + 20, cores: 8, frequency: 3200, temperature: Math.floor(Math.random() * 30) + 50, load1: Math.random() * 2, load5: Math.random() * 2, load15: Math.random() * 2 }),
  ram: () => ({ used: Math.floor(Math.random() * 8) + 4, total: 16, available: Math.floor(Math.random() * 4) + 2, cached: Math.floor(Math.random() * 2) + 1, swapUsed: Math.floor(Math.random() * 2), swapTotal: 4 }),
  gpu: () => ({ name: "NVIDIA RTX 4090", utilization: Math.floor(Math.random() * 50) + 30, vramUsed: Math.floor(Math.random() * 10) + 12, vramTotal: 24, temperature: Math.floor(Math.random() * 20) + 55, power: Math.floor(Math.random() * 100) + 250, frequency: Math.floor(Math.random() * 500) + 2000 }),
  providers: () => [
    { name: "Ollama", connected: true, latencyMs: Math.floor(Math.random() * 5) + 1 },
    { name: "OpenAI", connected: Math.random() > 0.2, latencyMs: Math.floor(Math.random() * 200) + 150 },
    { name: "OpenRouter", connected: Math.random() > 0.5, latencyMs: Math.floor(Math.random() * 300) + 200 },
    { name: "Anthropic", connected: Math.random() > 0.7, latencyMs: Math.floor(Math.random() * 250) + 180 },
  ],
  tokens: () => ({ used: Math.floor(Math.random() * 4000) + 2000, total: 8192, rate: Math.floor(Math.random() * 50) + 10, cost: Math.random() * 0.5, model: "gemma3:4b" }),
  agents: () => [
    { name: "planner", status: "run" as const },
    { name: "executor", status: "run" as const },
    { name: "memory", status: "idle" as const },
    { name: "learning", status: "sleep" as const },
    { name: "reflective", status: "sleep" as const },
    { name: "autonomy", status: "sleep" as const },
  ],
  planner: () => ({ objective: "Optimiser pipeline RAG", tasksDone: Math.floor(Math.random() * 5) + 1, tasksTotal: 8, nextStep: "embed.chunk → memory.store" }),
  knowledge: () => ({ entries: Math.floor(Math.random() * 500) + 2000, skills: Math.floor(Math.random() * 10) + 15, contextUsed: Math.floor(Math.random() * 3000) + 2000, contextTotal: 8192, embeddings: Math.floor(Math.random() * 1000) + 1500 }),
  memory: () => ({ entries: Math.floor(Math.random() * 500) + 2000, redisKeys: Math.floor(Math.random() * 100) + 200, postgresEvents: Math.floor(Math.random() * 10000) + 50000, sizeMb: Math.floor(Math.random() * 500) + 200, hitRate: Math.floor(Math.random() * 10) + 88 }),
  mcp: () => ({ toolsAvailable: 24, toolsCalled: Math.floor(Math.random() * 100) + 50, successRate: Math.floor(Math.random() * 5) + 94, avgLatency: Math.floor(Math.random() * 50) + 20, errors: Math.floor(Math.random() * 3) }),
  plugins: () => [
    { name: "security", active: true, version: "1.2.0" },
    { name: "browser", active: true, version: "2.0.1" },
    { name: "twitter", active: Math.random() > 0.3, version: "1.5.0" },
    { name: "slack", active: true, version: "1.1.0" },
    { name: "docker", active: true, version: "3.0.0" },
    { name: "github", active: Math.random() > 0.5, version: "1.0.0" },
    { name: "notion", active: false, version: "0.9.0" },
    { name: "telegram", active: true, version: "1.3.0" },
  ],
  events: () => ({ total: Math.floor(Math.random() * 10000) + 50000, rate: Math.floor(Math.random() * 10) + 5, errors: Math.floor(Math.random() * 5), warnings: Math.floor(Math.random() * 10) }),
  network: () => ({ latency: Math.floor(Math.random() * 50) + 10, bandwidth: Math.floor(Math.random() * 500) + 800, packetsIn: Math.floor(Math.random() * 1000) + 5000, packetsOut: Math.floor(Math.random() * 1000) + 3000, errors: Math.floor(Math.random() * 3) }),
};

// ───────── Sparkline generators ─────────
const generateSparkline = (): number[] => {
  const points = 20;
  const base = Math.random() * 50 + 20;
  return Array.from({ length: points }, (_, i) =>
    Math.max(5, Math.min(100, base + Math.sin(i * 0.5) * 15 + (Math.random() - 0.5) * 20))
  );
};

// ───────── Sortable card wrapper ─────────
function SortableCard({ id }: { id: string }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const Card = CARD_REGISTRY[id];
  const data = MOCK_DATA[id]?.();
  const sparkline = useMemo(() => generateSparkline(), []);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  if (!Card) return null;

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <Card data={data} sparkline={sparkline} />
    </div>
  );
}

// ───────── Dashboard Grid ─────────
export function DashboardGrid() {
  const { layout, updateLayout, loaded } = useDashboardLayout();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (over && active.id !== over.id) {
        const oldIndex = layout.indexOf(active.id as string);
        const newIndex = layout.indexOf(over.id as string);
        const newLayout = [...layout];
        newLayout.splice(oldIndex, 1);
        newLayout.splice(newIndex, 0, active.id as string);
        updateLayout(newLayout);
      }
    },
    [layout, updateLayout]
  );

  if (!loaded) {
    return (
      <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
        {layout.map((id) => (
          <div key={id} className="rounded-xl border border-line-1 bg-background p-4">
            <Skeleton variant="text" lines={3} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => updateLayout(DEFAULT_LAYOUT)}
        >
          ↺ Reset layout
        </Button>
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={layout} strategy={verticalListSortingStrategy}>
          <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
            {layout.map((id) => (
              <SortableCard key={id} id={id} />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
}