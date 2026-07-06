"use client";

import { useStore } from "@/lib/store";
import { MissionControlPage } from "@/components/pages/mission-control";
import { GoalsPage } from "@/components/pages/goals-list";
import { MemoryExplorerPage } from "@/components/pages/memory-explorer";
import { SkillsLabPage } from "@/components/pages/skills-lab";
import { SystemMonitorPage } from "@/components/pages/system-monitor";
import { ApprovalsGovernancePage } from "@/components/pages/approvals-governance";
import { ChatViewPage } from "@/components/pages/chat-view";
const pages: Record<string, React.FC> = {
  "mission-control": MissionControlPage,
  goals: GoalsPage,
  memory: MemoryExplorerPage,
  skills: SkillsLabPage,
  monitor: SystemMonitorPage,
  approvals: ApprovalsGovernancePage,
  chat: ChatViewPage,
};

export default function Home() {
  const currentPage = useStore((s) => s.currentPage);
  const Page = pages[currentPage] || MissionControlPage;
  return <Page />;
}