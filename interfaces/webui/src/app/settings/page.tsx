"use client";

import * as React from "react";
import { SettingsWorkspace } from "@/components/features/settings/components/settings-workspace";

export default function SettingsPage() {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <SettingsWorkspace />
    </div>
  );
}