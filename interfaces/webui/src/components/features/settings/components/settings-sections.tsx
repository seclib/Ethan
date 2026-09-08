/**
 * ETHAN WebUI — Additional Settings Sections
 *
 * New sections for the reorganized settings:
 * - Chat (conversation configuration)
 * - AI (system configuration for AI models/providers)
 * - Search (search configuration)
 * - Reminders (reminder preferences)
 * - Shortcuts (keyboard shortcuts)
 * - Library (library preferences)
 * - System (system configuration)
 * - Security (security settings)
 * - Advanced (advanced configuration)
 *
 * Each setting has one owner and one source of truth:
 * - system: Core configuration (ConfigurationService)
 * - user: User preferences (WebUI store)
 * - project: Project configuration (ProjectManager)
 * - conversation: Conversation settings (ChatStore)
 */

"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// ── Chat Section (conversation configuration) ────────────────────────

export function ChatSection() {
  return (
    <div className="p-6">
      <SectionHeader title="Chat" description="Conversation configuration and preferences." />
      <div className="space-y-4">
        <SettingRow title="Default Chat Mode" description="Choose the default mode for new conversations" owner="conversation">
          <select className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground">
            <option>Standard</option>
            <option>Creative</option>
            <option>Precise</option>
          </select>
        </SettingRow>
        <SettingRow title="Message History" description="Number of messages to keep in context" owner="conversation">
          <Input type="number" defaultValue={50} className="w-24" />
        </SettingRow>
        <SettingRow title="Auto-save Drafts" description="Automatically save conversation drafts" owner="user">
          <ToggleSwitch defaultChecked />
        </SettingRow>
      </div>
    </div>
  );
}

// ── AI Section (system configuration) ────────────────────────────────

export function AISection() {
  return (
    <div className="p-6">
      <SectionHeader title="AI" description="AI model and provider configuration." />
      <div className="space-y-4">
        <SettingRow title="Default Model" description="The default AI model for new conversations" owner="system">
          <select className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground">
            <option>gpt-4</option>
            <option>claude-3</option>
            <option>llama-3</option>
          </select>
        </SettingRow>
        <SettingRow title="Temperature" description="Controls randomness (0.0 - 2.0)" owner="system">
          <Input type="number" defaultValue={0.7} step={0.1} className="w-24" />
        </SettingRow>
        <SettingRow title="Max Tokens" description="Maximum response length" owner="system">
          <Input type="number" defaultValue={4096} className="w-24" />
        </SettingRow>
        <SettingRow title="Streaming" description="Stream responses in real-time" owner="system">
          <ToggleSwitch defaultChecked />
        </SettingRow>
      </div>
    </div>
  );
}

// ── Search Section (search configuration) ─────────────────────────────

export function SearchSection() {
  return (
    <div className="p-6">
      <SectionHeader title="Search" description="Search configuration and preferences." />
      <div className="space-y-4">
        <SettingRow title="Default Search Type" description="The default search type for the command palette" owner="user">
          <select className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground">
            <option>knowledge</option>
            <option>library</option>
            <option>conversation</option>
            <option>web</option>
          </select>
        </SettingRow>
        <SettingRow title="Search Results Limit" description="Maximum number of results to display" owner="user">
          <Input type="number" defaultValue={20} className="w-24" />
        </SettingRow>
        <SettingRow title="Fuzzy Matching" description="Enable fuzzy text matching in search" owner="system">
          <ToggleSwitch defaultChecked />
        </SettingRow>
      </div>
    </div>
  );
}

// ── Shortcuts Section (UI-only keyboard shortcuts) ─────────────────────
//
// These are display/navigation shortcuts handled entirely by the WebUI
// (use-keyboard.ts hook). They dispatch to routes and never invoke
// Runtime business logic directly. The authoritative shortcut registry
// lives in @/config/shortcuts.ts.

import { SHORTCUTS } from "@/config/shortcuts";
import { Keyboard } from "lucide-react";

export function ShortcutsSection() {
  return (
    <div className="p-6">
      <SectionHeader
        title="Shortcuts"
        description="Keyboard shortcuts for quick navigation (UI-only — managed by WebUI)."
      />
      <div className="space-y-2">
        {SHORTCUTS.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between rounded-md border border-line-1 px-4 py-3"
          >
            <div className="flex items-center gap-2">
              <Keyboard className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-foreground">{s.label}</span>
            </div>
            <kbd className="rounded-md bg-[var(--panel)] px-2 py-1 text-xs font-mono text-muted-foreground">
              {s.display}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Library Section (project configuration — library preferences) ──────

// ── Library Section (project configuration) ───────────────────────────

export function LibrarySection() {
  return (
    <div className="p-6">
      <SectionHeader title="Library" description="Library preferences and defaults." />
      <div className="space-y-4">
        <SettingRow title="Default View" description="Default library view mode" owner="user">
          <select className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground">
            <option>Grid</option>
            <option>List</option>
          </select>
        </SettingRow>
        <SettingRow title="Auto-refresh" description="Automatically refresh library contents" owner="user">
          <ToggleSwitch defaultChecked />
        </SettingRow>
        <SettingRow title="Show Preview" description="Show item preview panel by default" owner="user">
          <ToggleSwitch defaultChecked />
        </SettingRow>
      </div>
    </div>
  );
}

// ── System Section (system configuration) ─────────────────────────────

export function SystemSection() {
  return (
    <div className="p-6">
      <SectionHeader title="System" description="System-level configuration." />
      <div className="space-y-4">
        <SettingRow title="Log Level" description="Application logging level" owner="system">
          <select className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground">
            <option>INFO</option>
            <option>DEBUG</option>
            <option>WARN</option>
            <option>ERROR</option>
          </select>
        </SettingRow>
        <SettingRow title="Max Workers" description="Maximum number of background workers" owner="system">
          <Input type="number" defaultValue={4} className="w-24" />
        </SettingRow>
        <SettingRow title="Telemetry" description="Send anonymous usage statistics" owner="system">
          <ToggleSwitch />
        </SettingRow>
      </div>
    </div>
  );
}

// ── Security Section (system configuration) ───────────────────────────

export function SecuritySection() {
  return (
    <div className="p-6">
      <SectionHeader title="Security" description="Security settings and permissions." />
      <div className="space-y-4">
        <SettingRow title="Two-Factor Authentication" description="Require 2FA for all users" owner="system">
          <ToggleSwitch />
        </SettingRow>
        <SettingRow title="Session Timeout" description="Automatically log out after inactivity" owner="system">
          <div className="flex items-center gap-2">
            <Input type="number" defaultValue={30} className="w-20" />
            <span className="text-sm text-muted-foreground">minutes</span>
          </div>
        </SettingRow>
        <SettingRow title="API Key Rotation" description="Automatically rotate API keys" owner="system">
          <ToggleSwitch />
        </SettingRow>
      </div>
    </div>
  );
}

// ── Advanced Section (system configuration) ───────────────────────────

export function AdvancedSection() {
  return (
    <div className="p-6">
      <SectionHeader title="Advanced" description="Advanced configuration options." />
      <div className="space-y-4">
        <SettingRow title="Experimental Features" description="Enable experimental features" owner="system">
          <ToggleSwitch />
        </SettingRow>
        <SettingRow title="Debug Mode" description="Enable debug logging and tools" owner="system">
          <ToggleSwitch />
        </SettingRow>
        <SettingRow title="Custom CSS" description="Add custom styles to the interface" owner="user">
          <Button size="sm" variant="outline">Edit CSS</Button>
        </SettingRow>
      </div>
    </div>
  );
}

// ── Shared Components ─────────────────────────────────────────────────

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-xl font-bold text-foreground">{title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function SettingRow({
  title,
  description,
  owner,
  children,
}: {
  title: string;
  description: string;
  owner: "system" | "user" | "project" | "conversation";
  children: React.ReactNode;
}) {
  const ownerColors = {
    system: "bg-blue-500/10 text-blue-400",
    user: "bg-green-500/10 text-green-400",
    project: "bg-yellow-500/10 text-yellow-400",
    conversation: "bg-purple-500/10 text-purple-400",
  };

  return (
    <div className="flex items-center justify-between rounded-md border border-line-1 px-4 py-3">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-foreground">{title}</h3>
          <span className={cn("rounded-full px-2 py-0.5 text-xs", ownerColors[owner])}>
            {owner}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="ml-4">{children}</div>
    </div>
  );
}

function ToggleSwitch({ defaultChecked = false }: { defaultChecked?: boolean }) {
  const [checked, setChecked] = React.useState(defaultChecked);
  return (
    <button
      onClick={() => setChecked(!checked)}
      className={cn(
        "relative h-6 w-11 rounded-full transition-colors",
        checked ? "bg-[var(--accent)]" : "bg-[var(--panel-hover)]",
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform",
          checked && "translate-x-5",
        )}
      />
    </button>
  );
}

export function RemindersSection() {
  return (
    <div className="p-6">
      <SectionHeader title="Reminders" description="Reminder preferences and defaults." />
      <div className="space-y-4">
        <SettingRow title="Default Timezone" description="Default timezone for new reminders" owner="user">
          <select className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground">
            <option>UTC</option>
            <option>America/New_York</option>
            <option>Europe/Paris</option>
            <option>Asia/Tokyo</option>
          </select>
        </SettingRow>
        <SettingRow title="Notification Sound" description="Play a sound when reminders fire" owner="user">
          <ToggleSwitch defaultChecked />
        </SettingRow>
        <SettingRow title="Auto-dismiss" description="Automatically dismiss reminders after" owner="user">
          <div className="flex items-center gap-2">
            <Input type="number" defaultValue={5} className="w-20" />
            <span className="text-sm text-muted-foreground">minutes</span>
          </div>
        </SettingRow>
      </div>
    </div>
  );
}
