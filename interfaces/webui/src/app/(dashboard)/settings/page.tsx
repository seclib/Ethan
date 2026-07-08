import * as React from "react";
import { Card } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          System configuration and governance
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <h3 className="font-semibold">LLM Configuration</h3>
          <p className="text-sm text-muted-foreground mt-2">Model, temperature, max tokens</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">Permissions & Governance</h3>
          <p className="text-sm text-muted-foreground mt-2">Access levels, approval modes</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">Budget</h3>
          <p className="text-sm text-muted-foreground mt-2">Daily limits, cost tracking</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">System</h3>
          <p className="text-sm text-muted-foreground mt-2">Theme, language, notifications</p>
        </Card>
      </div>
    </div>
  );
}