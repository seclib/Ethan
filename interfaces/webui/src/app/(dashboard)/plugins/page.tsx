"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useUIStore } from "@/core/store/ui.store";
import { Search, Plus } from "lucide-react";

export default function PluginsPage() {
  const [plugins, setPlugins] = React.useState([
    { id: "docker", name: "Docker Builder", version: "1.0.0", enabled: true },
    { id: "k8s", name: "Kubernetes Deploy", version: "0.9.0", enabled: true },
    { id: "web", name: "Web Scraper", version: "2.1.0", enabled: false },
    { id: "slack", name: "Slack Notifier", version: "1.2.0", enabled: false },
  ]);
  const [search, setSearch] = React.useState("");
  const addToast = useUIStore((s) => s.addToast);

  const notImplemented = () => {
    addToast({ type: "info", message: "Feature not implemented yet" });
  };

  const togglePlugin = (id: string) => {
    setPlugins((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    );
  };

  const filtered = plugins.filter((p) => p.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Plugins</h1>
          <p className="text-foreground-secondary mt-2">Plugin marketplace and management</p>
        </div>
        <Button variant="primary" icon={<Plus className="w-4 h-4" />} onClick={notImplemented}>Install</Button>
      </div>

      <Input placeholder="Search plugins..." value={search} onChange={(e) => setSearch(e.target.value)} icon={<Search className="w-4 h-4" />} />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((plugin) => (
          <Card key={plugin.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{plugin.name}</CardTitle>
                <Badge variant={plugin.enabled ? "success" : "dim"} size="sm" dot>{plugin.enabled ? "Enabled" : "Disabled"}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-foreground-tertiary mb-3">v{plugin.version}</p>
              <Button
                size="sm"
                variant={plugin.enabled ? "secondary" : "primary"}
                onClick={() => togglePlugin(plugin.id)}
              >
                {plugin.enabled ? "Disable" : "Enable"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}