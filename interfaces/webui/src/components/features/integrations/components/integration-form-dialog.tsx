"use client";

/**
 * IntegrationFormDialog — création / configuration d'une intégration.
 *
 * Le WebUI ne gère que la CONFIGURATION :
 * - identity (name + kind) : figée à la création, jamais modifiable ;
 * - config : dict générique édité en JSON (validé localement avant envoi) ;
 * - credentials : paires clé/valeur saisies à la main — JAMAIS pré-remplies
 *   (l'API ne renvoie jamais les valeurs, seulement `credential_keys`) ;
 * - required_permissions : choix restreint aux permissions ETHAN réelles
 *   (core.auth.Permission) — une intégration ne peut pas inventer ses droits.
 */

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Save, X, Plus, Trash2 } from "lucide-react";
import type {
  Integration,
  IntegrationCreate,
  IntegrationKind,
  IntegrationUpdate,
} from "@/lib/api/integrations";

/** Permissions ETHAN réelles (miroir de core.auth.Permission — validation côté Core). */
export const ETHAN_PERMISSIONS = [
  { value: "read", label: "Read" },
  { value: "write", label: "Write" },
  { value: "admin", label: "Admin" },
  { value: "chat", label: "Chat" },
  { value: "agents", label: "Agents" },
  { value: "memory", label: "Memory" },
  { value: "plugins", label: "Plugins" },
  { value: "settings", label: "Settings" },
  { value: "files", label: "Files" },
  { value: "execute", label: "Execute" },
] as const;

const KIND_OPTIONS: { value: IntegrationKind; label: string }[] = [
  { value: "mcp", label: "MCP (Model Context Protocol)" },
  { value: "web-search", label: "Web Search" },
  { value: "storage", label: "Storage (S3, GDrive…)" },
  { value: "automation", label: "Automation (n8n, Zapier…)" },
  { value: "developer", label: "Developer services (GitHub, CI…)" },
  { value: "external-app", label: "External application" },
];

interface Props {
  open: boolean;
  mode: "create" | "edit";
  integration: Integration | null;
  onClose: () => void;
  onCreate: (data: IntegrationCreate) => Promise<void>;
  onUpdate: (id: string, data: IntegrationUpdate) => Promise<void>;
}

interface CredentialRow {
  key: string;
  value: string;
}

export function IntegrationFormDialog({ open, mode, integration, onClose, onCreate, onUpdate }: Props) {
  const [name, setName] = React.useState("");
  const [kind, setKind] = React.useState<IntegrationKind>("mcp");
  const [description, setDescription] = React.useState("");
  const [configJson, setConfigJson] = React.useState("{}");
  const [capabilities, setCapabilities] = React.useState("");
  const [permissions, setPermissions] = React.useState<string[]>([]);
  const [credentialRows, setCredentialRows] = React.useState<CredentialRow[]>([]);
  const [enabled, setEnabled] = React.useState(true);
  const [configError, setConfigError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Pré-remplissage (mode edit) — les credentials ne sont JAMAIS pré-remplis.
  React.useEffect(() => {
    if (!open) return;
    if (mode === "edit" && integration) {
      setName(integration.name);
      setKind(integration.kind);
      setDescription(integration.description ?? "");
      setConfigJson(JSON.stringify(integration.config ?? {}, null, 2));
      setCapabilities((integration.capabilities ?? []).join(", "));
      setPermissions([...(integration.required_permissions ?? [])]);
      setCredentialRows([]);
      setEnabled(integration.enabled);
    } else {
      setName("");
      setKind("mcp");
      setDescription("");
      setConfigJson("{}");
      setCapabilities("");
      setPermissions([]);
      setCredentialRows([]);
      setEnabled(true);
    }
    setConfigError(null);
  }, [open, mode, integration]);

  const togglePermission = (value: string) => {
    setPermissions((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value],
    );
  };

  const updateRow = (index: number, patch: Partial<CredentialRow>) => {
    setCredentialRows((prev) => prev.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  };

  const handleSubmit = async () => {
    // Validation locale du JSON de config (le Core revalide).
    let config: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(configJson || "{}");
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("config must be a JSON object");
      }
      config = parsed as Record<string, unknown>;
      setConfigError(null);
    } catch (err) {
      setConfigError(err instanceof Error ? err.message : "Invalid JSON");
      return;
    }

    // Credentials : seules les paires complètes et non vides sont envoyées.
    const credentials: Record<string, string> = {};
    for (const row of credentialRows) {
      const key = row.key.trim();
      if (key && row.value.trim()) credentials[key] = row.value.trim();
    }

    const capabilityList = capabilities
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);

    setIsSubmitting(true);
    try {
      if (mode === "create") {
        await onCreate({
          name: name.trim(),
          kind,
          description: description.trim(),
          config,
          credentials: Object.keys(credentials).length ? credentials : undefined,
          capabilities: capabilityList,
          required_permissions: permissions,
          enabled,
        });
      } else if (integration) {
        const data: IntegrationUpdate = {
          description: description.trim(),
          config,
          capabilities: capabilityList,
          required_permissions: permissions,
          enabled,
        };
        // Rotation : uniquement si l'utilisateur a saisi de nouvelles valeurs.

  return (
    <Dialog open={open} onClose={onClose} title={title} size="lg">
      <div className="flex flex-col gap-4">
        {/* Identity — stable, jamais modifiable en édition */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Nom</label>
            <Input
              placeholder="ex: github-prod"
              value={name}
              disabled={mode === "edit"}
              onChange={(e) => setName(e.target.value)}
            />
            {mode === "edit" && (
              <p className="mt-1 text-xs text-foreground-tertiary">
                Identité stable — non modifiable.
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Type</label>
            <select
              className="w-full rounded-lg border border-line-2 bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
              value={kind}
              disabled={mode === "edit"}
              onChange={(e) => setKind(e.target.value as IntegrationKind)}
            >
              {KIND_OPTIONS.map((k) => (
                <option key={k.value} value={k.value}>
                  {k.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <Input
            placeholder="À quoi sert cette intégration"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* Configuration (JSON) */}
        <div>
          <label className="mb-1 block text-sm font-medium">Configuration (JSON)</label>
          <textarea
            className="w-full rounded-lg border border-line-2 bg-background px-3 py-2 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-accent-400"
            rows={4}
            spellCheck={false}
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
          />
          {configError && <p className="mt-1 text-xs text-red-500">{configError}</p>}
        </div>
        if (Object.keys(credentials).length) data.credentials = credentials;
        await onUpdate(integration.id, data);

        {/* Credentials — jamais pré-remplis (seules les clés sont connues du front) */}
        <div>
          <div className="mb-1 flex items-center justify-between">
            <label className="block text-sm font-medium">
              Credentials
              <span className="ml-2 text-xs font-normal text-foreground-tertiary">
                (stockés côté Core — jamais affichés ni renvoyés)
              </span>
            </label>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCredentialRows((prev) => [...prev, { key: "", value: "" }])}
            >
              <Plus className="h-3 w-3" /> Ajouter
            </Button>
          </div>
          {mode === "edit" && (integration?.credential_keys?.length ?? 0) > 0 && (
            <p className="mb-1 text-xs text-foreground-tertiary">
              Clés existantes : {integration?.credential_keys.join(", ")} — laissez vide pour
              conserver.
            </p>
          )}
          {credentialRows.length === 0 ? (
            <p className="text-xs text-muted-foreground">Aucun credential à définir.</p>
          ) : (
            <div className="space-y-2">
              {credentialRows.map((row, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Input
                    placeholder="clé (ex: token)"
                    className="flex-1"
                    value={row.key}
                    onChange={(e) => updateRow(index, { key: e.target.value })}
                  />
                  <Input
                    type="password"
                    placeholder="valeur"
                    className="flex-1"
                    value={row.value}
                    onChange={(e) => updateRow(index, { value: e.target.value })}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label="Retirer ce credential"
                    onClick={() =>
                      setCredentialRows((prev) => prev.filter((_, i) => i !== index))
                    }
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Capabilities */}
        <div>
          <label className="mb-1 block text-sm font-medium">
            Capacités déclarées
            <span className="ml-2 text-xs font-normal text-foreground-tertiary">
              (séparées par des virgules, ex: repos.read, issues.write)
            </span>
          </label>
          <Input
            placeholder="repos.read, issues.write"
            value={capabilities}
            onChange={(e) => setCapabilities(e.target.value)}
          />
        </div>

        {/* Permissions ETHAN requises */}
        <div>
          <label className="mb-1 block text-sm font-medium">
            Permissions ETHAN requises
            <span className="ml-2 text-xs font-normal text-foreground-tertiary">
              (validées par le Core — appliquées par le Runtime)
            </span>
          </label>
          <div className="flex flex-wrap gap-2">
            {ETHAN_PERMISSIONS.map((perm) => {
              const active = permissions.includes(perm.value);
              return (
                <button
                  key={perm.value}
                  type="button"
                  onClick={() => togglePermission(perm.value)}
                  aria-pressed={active}
                  className={
                    active
                      ? "rounded-full border border-accent bg-accent/15 px-3 py-1 text-xs font-medium text-accent"
                      : "rounded-full border border-line-2 px-3 py-1 text-xs text-foreground-secondary hover:border-accent/40"
                  }
                >
                  {perm.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Enabled */}
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="h-4 w-4"
          />
          Activée (une intégration désactivée ne peut pas être connectée)
        </label>

        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" size="sm" onClick={onClose}>
            <X className="h-4 w-4" /> Annuler
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting || (mode === "create" && !name.trim())}
          >
            <Save className="h-4 w-4" /> {mode === "create" ? "Créer" : "Enregistrer"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
      }
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const title = mode === "create" ? "Nouvelle intégration" : `Configurer — ${integration?.name ?? ""}`;
}