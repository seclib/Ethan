"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function TerminalPage() {
  const [history, setHistory] = React.useState<string[]>([
    "ETHAN Shell v1.0",
    "Type 'help' for available commands",
  ]);
  const [input, setInput] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setHistory((prev) => [...prev, `$ ${input}`, `[${input}]: executed`]);
    setInput("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Terminal</h1>
        <p className="text-foreground-secondary mt-2">ETHAN Shell interface</p>
      </div>

      <Card variant="outlined" className="font-mono text-sm">
        <CardContent className="p-4">
          <div className="h-[400px] overflow-y-auto mb-4 space-y-1">
            {history.map((line, i) => (
              <div key={i} className={line.startsWith("$") ? "text-accent" : "text-foreground"}>
                {line}
              </div>
            ))}
          </div>
          <form onSubmit={handleSubmit}>
            <div className="flex items-center gap-2">
              <span className="text-accent shrink-0">$</span>
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a command..."
                className="border-0 bg-transparent p-0 focus:ring-0"
              />
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}