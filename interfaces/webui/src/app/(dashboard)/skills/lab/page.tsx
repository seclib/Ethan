"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSkills } from "@/hooks/use-skills";
import { getStatusColor } from "@/lib/utils";

export default function SkillsLabPage() {
  const { skills, isLoading, error } = useSkills();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Skills Lab</h1>
          <p className="text-muted-foreground mt-2">Loading skills...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Skills Lab</h1>
          <p className="text-destructive mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Skills Lab</h1>
        <p className="text-muted-foreground mt-2">
          Test, validate, and install skills
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Skill Candidates</h3>
          <p className="text-2xl font-bold">
            {skills.filter((s) => s.status === "candidate").length}
          </p>
          <p className="text-sm text-muted-foreground">In testing phase</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Installed Skills</h3>
          <p className="text-2xl font-bold">
            {skills.filter((s) => s.status === "active").length}
          </p>
          <p className="text-sm text-muted-foreground">Active skills</p>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Skills</h3>
          {skills.length === 0 ? (
            <p className="text-sm text-muted-foreground">No skills yet</p>
          ) : (
            <div className="space-y-3">
              {skills.map((skill) => (
                <div
                  key={skill.id}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex-1">
                    <h4 className="font-medium">{skill.name}</h4>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {skill.description}
                    </p>
                    <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                      <span>v{skill.version}</span>
                      <span>•</span>
                      <span>Confidence: {Math.round(skill.confidence * 100)}%</span>
                    </div>
                  </div>
                  <Badge variant={getStatusColor(skill.status)}>
                    {skill.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}