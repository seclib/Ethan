"use client";

import { useStore } from "@/lib/store";
import { DashboardPage } from "@/components/pages/dashboard";
import { AssistantPage } from "@/components/pages/assistant";
import { KnowledgePage } from "@/components/pages/knowledge";
import { MemoryPage } from "@/components/pages/memory";
import { AgentsPage } from "@/components/pages/agents";
import { PlannerPage } from "@/components/pages/planner";
import { ModelsPage } from "@/components/pages/models";
import { ProvidersPage } from "@/components/pages/providers";
import { PluginsPage } from "@/components/pages/plugins";
import { ToolsPage } from "@/components/pages/tools";
import { DocumentsPage } from "@/components/pages/documents";
import { SettingsPage } from "@/components/pages/settings";
import { LogsPage } from "@/components/pages/logs";
import { TerminalPage } from "@/components/pages/terminal";

const pages: Record<string, React.FC> = {
  dashboard: DashboardPage,
  assistant: AssistantPage,
  knowledge: KnowledgePage,
  memory: MemoryPage,
  agents: AgentsPage,
  planner: PlannerPage,
  models: ModelsPage,
  providers: ProvidersPage,
  plugins: PluginsPage,
  tools: ToolsPage,
  documents: DocumentsPage,
  settings: SettingsPage,
  logs: LogsPage,
  terminal: TerminalPage,
};

export default function Home() {
  const currentPage = useStore((s) => s.currentPage);
  const Page = pages[currentPage] || DashboardPage;
  return <Page />;
}