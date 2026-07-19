"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function DocumentsPage() {
  const [search, setSearch] = React.useState("");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Documents</h1>
        <p className="text-foreground-secondary mt-2">Manage files, ingestions, and RAG sources.</p>
      </div>

      <div className="flex gap-2">
        <Input placeholder="Search documents..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>No documents yet</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground-tertiary">Upload documents to analyze.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
