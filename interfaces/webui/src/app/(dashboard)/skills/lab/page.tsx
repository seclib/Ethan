import * as React from "react";
import { Card } from "@/components/ui/card";

export default function SkillsLabPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Skills Lab</h1>
        <p className="text-muted-foreground mt-2">
          Test, validate, and install skills
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Skill Candidates</h3>
            <p className="text-sm text-muted-foreground mt-2">No skills in testing</p>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Installed Skills</h3>
            <p className="text-sm text-muted-foreground mt-2">Coming soon</p>
          </div>
        </Card>
      </div>
    </div>
  );
}