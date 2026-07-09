import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-foreground-secondary mt-2">
          System configuration and governance
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card variant="outlined" hoverable>
          <CardHeader>
            <CardTitle>LLM Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground-tertiary">Model, temperature, max tokens</p>
          </CardContent>
        </Card>
        <Card variant="outlined" hoverable>
          <CardHeader>
            <CardTitle>Permissions & Governance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground-tertiary">Access levels, approval modes</p>
          </CardContent>
        </Card>
        <Card variant="outlined" hoverable>
          <CardHeader>
            <CardTitle>Budget</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground-tertiary">Daily limits, cost tracking</p>
          </CardContent>
        </Card>
        <Card variant="outlined" hoverable>
          <CardHeader>
            <CardTitle>System</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground-tertiary">Theme, language, notifications</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}