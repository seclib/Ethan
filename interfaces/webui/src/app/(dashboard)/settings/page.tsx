"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/core/api/api-client";
import { useUIStore } from "@/core/store/ui.store";

interface Settings {
  llm: { provider: string; model: string; temperature: number };
  permissions: { allow_autonomy: boolean; allow_network: boolean };
  budget: { daily_limit_usd: number; alert_threshold: number };
  system: { log_level: string; max_workers: number };
}

type SectionKey = keyof Settings;

const SECTIONS: { key: SectionKey; title: string; desc: string }[] = [
  { key: "llm", title: "LLM Configuration", desc: "Model, temperature, max tokens" },
  { key: "permissions", title: "Permissions & Governance", desc: "Access levels, approval modes" },
  { key: "budget", title: "Budget", desc: "Daily limits, cost tracking" },
  { key: "system", title: "System", desc: "Theme, language, notifications" },
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [editMode, setEditMode] = React.useState<SectionKey | null>(null);
  const [formData, setFormData] = React.useState<Settings | null>(null);

  const { data: settings, isLoading, error } = useQuery<Settings>({
    queryKey: ["settings"],
    queryFn: () => apiClient.request<Settings>("/api/v1/settings"),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Settings>) =>
      apiClient.request<Settings>("/api/v1/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      addToast({ type: "success", message: "Settings updated successfully" });
      setEditMode(null);
    },
    onError: (err) => {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update settings" });
    },
  });

  React.useEffect(() => {
    if (settings && !formData) {
      setFormData(settings);
    }
  }, [settings, formData]);

  const handleFieldChange = (key: SectionKey, field: string, value: unknown) => {
    if (!formData) return;
    const sectionData = formData[key] as unknown as Record<string, unknown>;
    setFormData({
      ...formData,
      [key]: { ...sectionData, [field]: value } as Settings[SectionKey],
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-foreground-secondary mt-2">System configuration and governance</p>
      </div>

      {isLoading && <p className="text-foreground-tertiary text-sm">Loading settings...</p>}
      {error && <p className="text-red/80 text-sm">Error: {error.message}</p>}

      {settings && (
        <div className="grid gap-4 md:grid-cols-2">
          {SECTIONS.map((section) => {
            const sectionData = settings[section.key] as unknown as Record<string, unknown>;
            const isEditing = editMode === section.key;
            return (
              <Card key={section.key} variant="outlined" hoverable>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{section.title}</CardTitle>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditMode(isEditing ? null : section.key)}
                      aria-label={`Edit ${section.title}`}
                    >
                      {isEditing ? "Cancel" : "Edit"}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-foreground-tertiary mb-3">{section.desc}</p>
                  <div className="space-y-2">
                    {Object.entries(sectionData).map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between text-xs">
                        <span className="text-foreground-tertiary font-mono">{k}</span>
                        {isEditing && formData ? (
                          <Input
                            type={typeof v === "number" ? "number" : "text"}
                            value={String(v)}
                            onChange={(e) => {
                              const newVal = typeof v === "number" ? Number(e.target.value) : e.target.value;
                              handleFieldChange(section.key, k, newVal);
                            }}
                            className="h-7 w-32 text-xs"
                          />
                        ) : (
                          <span className="text-foreground-secondary font-mono">{String(v)}</span>
                        )}
                      </div>
                    ))}
                  </div>
                  {isEditing && (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="mt-3"
                      onClick={() => {
                        if (formData) {
                          updateMutation.mutate({ [section.key]: formData[section.key] });
                        }
                      }}
                      disabled={updateMutation.isPending}
                      aria-label={`Save ${section.title}`}
                    >
                      {updateMutation.isPending ? "Saving..." : "Save"}
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}