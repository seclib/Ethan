import * as React from "react";
import { Card } from "@/components/ui/card";

export default function FluxPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Event Flux</h1>
        <p className="text-muted-foreground mt-2">
          Real-time event stream from the kernel
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Events Today</h3>
            <p className="text-2xl font-bold mt-2">0</p>
            <p className="text-sm text-muted-foreground">No events yet</p>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Throughput</h3>
            <p className="text-2xl font-bold mt-2">—</p>
            <p className="text-sm text-muted-foreground">events/minute</p>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Status</h3>
            <p className="text-2xl font-bold mt-2">●</p>
            <p className="text-sm text-muted-foreground">Connected</p>
          </div>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Live Event Stream</h3>
          <p className="text-sm text-muted-foreground">Waiting for events...</p>
        </div>
      </Card>
    </div>
  );
}