"use client";

import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TestTube, Puzzle, Bot } from "lucide-react";

const toolSections = [
  { id: "skills-lab", label: "Skills Lab", icon: TestTube, desc: "Test, validate, and install cognitive skills", href: "/tools/lab" },
  { id: "plugins", label: "Plugin Manager", icon: Puzzle, desc: "Manage installed plugins and extensions", href: "/plugins" },
  { id: "agents", label: "Agent Console", icon: Bot, desc: "Deploy and monitor cognitive agents", href: "/agents" },
];

export default function ToolsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Tools</h1>
        <p className="text-foreground-secondary mt-2">Orchestration and engine tooling</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {toolSections.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.id} variant="outlined" hoverable>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Icon size={20} className="text-accent" />
                  <CardTitle className="text-sm">{s.label}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-foreground-tertiary mb-3">{s.desc}</p>
                <Link href={s.href} className="text-xs font-mono text-accent hover:underline">Open →</Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}