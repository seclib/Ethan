"use client";

import { useStore } from "@/lib/store";
import { DashboardPage } from "@/components/legacy-pages/dashboard";
import AssistantPage from "@/components/legacy-pages/assistant";
import { KnowledgePage } from "@/components/legacy-pages/knowledge";
import { MemoryPage } from "@/components/legacy-pages/memory";
import { AgentsPage } from "@/components/legacy-pages/agents";
import { PlannerPage } from "@/components/legacy-pages/planner";
import { ModelsPage } from "@/components/legacy-pages/models";
import { ProvidersPage } from "@/components/legacy-pages/providers";
import { PluginsPage } from "@/components/legacy-pages/plugins";
import { ToolsPage } from "@/components/legacy-pages/tools";
import { DocumentsPage } from "@/components/legacy-pages/documents";
import { SettingsPage } from "@/components/legacy-pages/settings";
import { LogsPage } from "@/components/legacy-pages/logs";
import { TerminalPage } from "@/components/legacy-pages/terminal";

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