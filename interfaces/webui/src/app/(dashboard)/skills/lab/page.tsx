"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useSkills } from "@/hooks/use-skills";
import { getStatusColor } from "@/lib/utils";

export default function SkillsLabPage() {
  const { skills, isLoading, error } = useSkills();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Skills Lab</h1>
          <p className="text-foreground-secondary mt-2">Loading skills...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent>
                <Skeleton variant="text" lines={3} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Skills Lab</h1>
          <p className="text-error-600 mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  const candidateSkills = skills.filter((s: any) => s.status === "candidate").length;
  const activeSkills = skills.filter((s: any) => s.status === "active").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Skills Lab</h1>
        <p className="text-foreground-secondary mt-2">
          Test, validate, and install skills
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Skill Candidates</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{candidateSkills}</p>
            <p className="text-sm text-foreground-tertiary mt-1">In testing phase</p>
          </CardContent>
        </Card>
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Installed Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{activeSkills}</p>
            <p className="text-sm text-foreground-tertiary mt-1">Active skills</p>
          </CardContent>
        </Card>
      </div>

      <Card variant="outlined">
        <CardHeader>
          <CardTitle>Skills</CardTitle>
        </CardHeader>
        <CardContent>
          {skills.length === 0 ? (
            <p className="text-sm text-foreground-tertiary">No skills yet</p>
          ) : (
            <div className="space-y-3">
              {skills.map((skill: any) => (
                <div
                  key={skill.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-line-1 hover:border-line-2 transition-colors duration-100"
                >
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground">{skill.name}</h4>
                    <p className="text-sm text-foreground-tertiary line-clamp-1">
                      {skill.description}
                    </p>
                    <div className="flex gap-2 mt-1 text-xs text-foreground-tertiary">
                      <span>v{skill.version}</span>
                      <span>•</span>
                      <span>Confidence: {Math.round(skill.confidence * 100)}%</span>
                    </div>
                  </div>
                  <Badge variant={getStatusColor(skill.status)} dot>
                    {skill.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}