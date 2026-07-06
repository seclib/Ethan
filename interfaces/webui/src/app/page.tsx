"use client";

import { useStore } from "@/lib/store";
import { MissionControlPage } from "@/components/pages/mission-control";
import { GoalsPage } from "@/components/pages/goals-list";
import { MemoryExplorerPage } from "@/components/pages/memory-explorer";
import { SkillsLabPage } from "@/components/pages/skills-lab";
import { SystemMonitorPage } from "@/components/pages/system-monitor";
import { ApprovalsGovernancePage } from "@/components/pages/approvals-governance";
import { ChatViewPage } from "@/components/pages/chat-view";
import { BudgetPage } from "@/components/pages/budget";
import { AuditPage } from "@/components/pages/audit";
import { DebugPage } from "@/components/pages/debug";
import { EventsPage } from "@/components/pages/events";
import { FactsPage } from "@/components/pages/facts";
const pages: Record<string, React.FC> = {
  "mission-control": MissionControlPage,
  goals: GoalsPage,
  memory: MemoryExplorerPage,
  skills: SkillsLabPage,
  monitor: SystemMonitorPage,
  approvals: ApprovalsGovernancePage,
  chat: ChatViewPage,
  budget: BudgetPage,
  audit: AuditPage,
  debug: DebugPage,
  events: EventsPage,
  facts: FactsPage,
};

export default function Home() {
  const currentPage = useStore((s) => s.currentPage);
  const Page = pages[currentPage] || MissionControlPage;
  return <Page />;
}