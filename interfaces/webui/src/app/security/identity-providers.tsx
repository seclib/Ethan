"use client";

/**
 * IdentityProviders — administration SCIM / LDAP / OAuth (Section Sécurité).
 *
 * Connexions réelles (Core-owned : core/auth/{scim,ldap,oauth}.py) :
 *   SCIM  : GET/POST /v1/scim/config · GET /v1/scim/status
 *   LDAP  : GET/POST /v1/ldap/config · GET /v1/ldap/status
 *   OAuth : GET/POST /v1/oauth/providers · POST /v1/oauth/providers/{name}/disable
 *
 * Politique secrets (miroir du contrat API) : aucun secret n'est jamais
 * affiché ni re-renvoyé en clair. La lecture expose un booléen `<champ>_set`
 * (rendu « configuré ») ; à l'écriture, un champ secret laissé VIDE conserve
 * la valeur stockée par le Core. Aucune action non supportée par l'API
 * (pas de « tester la connexion », pas de suppression) n'est simulée.
 *
 * AGENTS.md : pure interface — toute la logique (validation, stockage,
 * hashing) vit dans le Core. Status / Configuration / Actions sont distincts.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getScimConfig, configureScim, getScimStatus,
  getLdapConfig, configureLdap, getLdapStatus,
  listOAuthProviders, registerOAuthProvider, disableOAuthProvider,
  type IdentityConfig, type OAuthProvider,
} from "@/lib/api/auth-providers";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { Settings2, KeyRound, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
/* ── Primitives partagées ────────────────────────────────────────────────── */

/** Pastille de statut — distincte de la configuration (règle audit). */
function StatusPill({ enabled }: { enabled: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium",
        enabled
          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-500"
          : "border-line-2 bg-elevated text-foreground-tertiary",
      )}
    >
      {enabled ? <ShieldCheck size={11} /> : <ShieldOff size={11} />}
      {enabled ? "Actif" : "Inactif"}
    </span>
  );
}

/** Champ texte de configuration (non sensible). */
function Field({
  label, value, onChange, placeholder, mono,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; mono?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-foreground-secondary">{label}</span>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={cn("h-8 text-xs", mono && "font-mono")}
      />
    </label>
  );
}

/**
 * Champ secret (write-only) : la valeur existante n'est JAMAIS affichée —
 * un badge `●●● défini` / `non défini` reflète le booléen `<f>_set` renvoyé
 * par l'API. Un champ laissé vide préserve le secret stocké dans le Core.
 */
function SecretField({
  label, isSet, value, onChange, keepHint,
}: {
  label: string; isSet: boolean; value: string;
  onChange: (v: string) => void; keepHint: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 flex items-center gap-2 text-xs font-medium text-foreground-secondary">
        {label}
        <span
          className={cn(
            "rounded border px-1 py-px font-mono text-[9px]",
            isSet
              ? "border-amber-500/40 bg-amber-500/10 text-amber-500"
              : "border-line-2 text-foreground-tertiary",
          )}
          title={isSet ? "Secret stocké dans le Core (jamais renvoyé)" : undefined}
        >
          {isSet ? "●●● défini" : "non défini"}
        </span>
      </span>
      <Input
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={isSet ? keepHint : "Définir un secret"}
        autoComplete="new-password"
        className="h-8 font-mono text-xs"
      />
    </label>
  );
}


/* ── SCIM ────────────────────────────────────────────────────────────────── */

function ScimSection() {
  const qc = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const cfg = useQuery({ queryKey: ["scim-config"], queryFn: getScimConfig });
  const status = useQuery({ queryKey: ["scim-status"], queryFn: getScimStatus });

  const [form, setForm] = React.useState({ base_url: "", bearer_token: "" });
  const [enabled, setEnabled] = React.useState(false);
  const loadedKey = React.useRef("");

  // Sync du formulaire avec la config chargée (une fois par fetch).
  React.useEffect(() => {
    const data = cfg.data;
    if (!data || loadedKey.current === String(cfg.dataUpdatedAt)) return;
    loadedKey.current = String(cfg.dataUpdatedAt);
    setForm({ base_url: data.base_url || "", bearer_token: "" });
    setEnabled(data.enabled);
  }, [cfg.data, cfg.dataUpdatedAt]);

  const save = useMutation({
    mutationFn: () =>
      configureScim({
        enabled,
        base_url: form.base_url.trim(),
        bearer_token: form.bearer_token || undefined,
      }),
    onSuccess: () => {
      addToast({ type: "success", message: "Configuration SCIM enregistrée." });
      setForm((f) => ({ ...f, bearer_token: "" }));
      qc.invalidateQueries({ queryKey: ["scim-config"] });
      qc.invalidateQueries({ queryKey: ["scim-status"] });
    },
    onError: (e: Error) =>
      addToast({ type: "error", message: `Échec SCIM : ${e.message}` }),
  });

  return (
    <section className="rounded-lg border border-line-2 bg-bg-1 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <KeyRound size={15} /> SCIM — Provisioning
        </h3>
        <StatusPill enabled={status.data?.enabled ?? cfg.data?.enabled ?? false} />
      </div>

      {cfg.isLoading ? (
        <div className="flex justify-center p-6"><Spinner /></div>
      ) : cfg.isError ? (
        <p className="text-xs text-destructive">
          Impossible de charger la configuration SCIM.
        </p>
      ) : (
        <div className="space-y-3">
          <Field
            label="URL de base"
            value={form.base_url}
            onChange={(v) => setForm((f) => ({ ...f, base_url: v }))}
            placeholder="https://scim.exemple.com/v2"
            mono
          />
          <SecretField
            label="Bearer token"
            isSet={!!cfg.data?.bearer_token_set}
            value={form.bearer_token}
            onChange={(v) => setForm((f) => ({ ...f, bearer_token: v }))}
            keepHint="Laisser vide pour conserver le token actuel"
          />
          <label className="flex items-center gap-2 text-xs text-foreground-secondary">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
            />

/* ── LDAP ────────────────────────────────────────────────────────────────── */

function LdapSection() {
  const qc = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const cfg = useQuery({ queryKey: ["ldap-config"], queryFn: getLdapConfig });
  const status = useQuery({ queryKey: ["ldap-status"], queryFn: getLdapStatus });

  const empty = {
    server_url: "", bind_dn: "", bind_password: "",
    user_search_base: "", user_search_filter: "", tls_enabled: true,
  };
  const [form, setForm] = React.useState(empty);
  const [enabled, setEnabled] = React.useState(false);
  const loadedKey = React.useRef("");

  React.useEffect(() => {
    const data = cfg.data;
    if (!data || loadedKey.current === String(cfg.dataUpdatedAt)) return;
    loadedKey.current = String(cfg.dataUpdatedAt);
    setForm({
      server_url: data.server_url || "",
      bind_dn: data.bind_dn || "",
      bind_password: "",
      user_search_base: data.user_search_base || "",
      user_search_filter: data.user_search_filter || "",
      tls_enabled: data.tls_enabled ?? true,
    });
    setEnabled(data.enabled);
  }, [cfg.data, cfg.dataUpdatedAt]);

  const save = useMutation({
    mutationFn: () =>
      configureLdap({
        enabled,
        server_url: form.server_url.trim(),
        bind_dn: form.bind_dn.trim(),
        bind_password: form.bind_password || undefined,
        user_search_base: form.user_search_base.trim(),
        user_search_filter: form.user_search_filter.trim() || undefined,
        tls_enabled: form.tls_enabled,
      }),
    onSuccess: () => {
      addToast({ type: "success", message: "Configuration LDAP enregistrée." });
      setForm((f) => ({ ...f, bind_password: "" }));
      qc.invalidateQueries({ queryKey: ["ldap-config"] });
      qc.invalidateQueries({ queryKey: ["ldap-status"] });
    },
    onError: (e: Error) =>
      addToast({ type: "error", message: `Échec LDAP : ${e.message}` }),
  });

  return (
    <section className="rounded-lg border border-line-2 bg-bg-1 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <Globe size={15} /> LDAP — Annuaire
        </h3>
        <StatusPill enabled={status.data?.enabled ?? cfg.data?.enabled ?? false} />
      </div>

      {cfg.isLoading ? (
        <div className="flex justify-center p-6"><Spinner /></div>
      ) : cfg.isError ? (
        <p className="text-xs text-destructive">
          Impossible de charger la configuration LDAP.
        </p>
      ) : (
        <div className="space-y-3">
          <Field
            label="URL du serveur"
            value={form.server_url}
            onChange={(v) => setForm((f) => ({ ...f, server_url: v }))}
            placeholder="ldaps://annuaire.exemple.com:636"
            mono
          />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field
              label="Bind DN"
              value={form.bind_dn}
              onChange={(v) => setForm((f) => ({ ...f, bind_dn: v }))}
              placeholder="cn=admin,dc=exemple,dc=com"
              mono
            />
            <SecretField
              label="Mot de passe bind"
              isSet={!!cfg.data?.bind_password_set}
              value={form.bind_password}
              onChange={(v) => setForm((f) => ({ ...f, bind_password: v }))}
              keepHint="Laisser vide pour conserver le mot de passe actuel"
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field
              label="Base de recherche utilisateurs"
              value={form.user_search_base}
              onChange={(v) => setForm((f) => ({ ...f, user_search_base: v }))}
              placeholder="ou=people,dc=exemple,dc=com"
              mono
            />
            <Field
              label="Filtre de recherche"
              value={form.user_search_filter}
              onChange={(v) => setForm((f) => ({ ...f, user_search_filter: v }))}
              placeholder="(uid={username})"
              mono
            />
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs text-foreground-secondary">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.tls_enabled}
                onChange={(e) => setForm((f) => ({ ...f, tls_enabled: e.target.checked }))}
              />
              TLS
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
              />
              Activer l&apos;authentification LDAP
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
              {save.isPending ? "Enregistrement…" : "Enregistrer"}
            </Button>
            {save.isError && (

/* ── OAuth ───────────────────────────────────────────────────────────────── */

function OAuthSection() {
  const qc = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const providers = useQuery({ queryKey: ["oauth-providers"], queryFn: listOAuthProviders });

  const [registerOpen, setRegisterOpen] = React.useState(false);
  const [detail, setDetail] = React.useState<OAuthProvider | null>(null);
  const [confirmDisable, setConfirmDisable] = React.useState<OAuthProvider | null>(null);
  const [form, setForm] = React.useState({
    name: "", client_id: "", client_secret: "",
    authorize_url: "", token_url: "", userinfo_url: "", scopes: "",
  });
  const formValid =
    form.name.trim() && form.client_id.trim() && form.client_secret.trim() &&
    form.authorize_url.trim() && form.token_url.trim() && form.userinfo_url.trim();

  const register = useMutation({
    mutationFn: () =>
      registerOAuthProvider({
        name: form.name.trim(),
        client_id: form.client_id.trim(),
        client_secret: form.client_secret,
        authorize_url: form.authorize_url.trim(),
        token_url: form.token_url.trim(),
        userinfo_url: form.userinfo_url.trim(),
        scopes: form.scopes.split(/[\s,]+/).filter(Boolean),
      }),
    onSuccess: () => {
      addToast({ type: "success", message: `Provider OAuth « ${form.name} » enregistré.` });
      setRegisterOpen(false);
      setForm({ name: "", client_id: "", client_secret: "", authorize_url: "", token_url: "", userinfo_url: "", scopes: "" });
      qc.invalidateQueries({ queryKey: ["oauth-providers"] });
    },
    onError: (e: Error) =>
      addToast({ type: "error", message: `Échec OAuth : ${e.message}` }),
  });

  const disable = useMutation({
    mutationFn: (p: OAuthProvider) => disableOAuthProvider(p.name),
    onSuccess: (p) => {
      addToast({ type: "success", message: `Provider « ${p.name} » désactivé.` });
      setConfirmDisable(null);
      qc.invalidateQueries({ queryKey: ["oauth-providers"] });
    },
    onError: (e: Error) =>
      addToast({ type: "error", message: `Échec : ${e.message}` }),
  });

  return (
    <section className="rounded-lg border border-line-2 bg-bg-1 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <Settings2 size={15} /> OAuth — Fournisseurs
        </h3>
        <Button size="sm" variant="outline" onClick={() => setRegisterOpen(true)}>
          Enregistrer un provider
        </Button>
      </div>

      {providers.isLoading ? (
        <div className="flex justify-center p-6"><Spinner /></div>
      ) : providers.isError ? (
        <p className="text-xs text-destructive">
          Impossible de charger les providers OAuth.
        </p>
      ) : !providers.data?.length ? (
        <p className="py-4 text-center text-xs text-foreground-tertiary">
          Aucun provider OAuth enregistré. Utilisez « Enregistrer un provider »
          pour connecter un fournisseur d&apos;identité externe.
        </p>
      ) : (
        <ul className="divide-y divide-line-1">
          {providers.data.map((p) => (
            <li key={p.id} className="flex items-center gap-3 py-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium">{p.name}</span>
                  <StatusPill enabled={p.enabled} />
                </div>
                <span className="block truncate font-mono text-[11px] text-foreground-tertiary">
                  {p.client_id} · secret {p.client_secret_set ? "défini" : "non défini"}

      {/* Dialog — enregistrement d'un provider */}
      <Dialog open={registerOpen} onClose={() => setRegisterOpen(false)} title="Enregistrer un provider OAuth" size="lg">
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Nom" value={form.name} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="github" />
            <Field label="Client ID" value={form.client_id} onChange={(v) => setForm((f) => ({ ...f, client_id: v }))} mono />
          </div>
          <SecretField
            label="Client secret" isSet={false} value={form.client_secret}
            onChange={(v) => setForm((f) => ({ ...f, client_secret: v }))}
            keepHint=""
          />
          <Field label="Authorize URL" value={form.authorize_url} onChange={(v) => setForm((f) => ({ ...f, authorize_url: v }))} mono />
          <Field label="Token URL" value={form.token_url} onChange={(v) => setForm((f) => ({ ...f, token_url: v }))} mono />
          <Field label="Userinfo URL" value={form.userinfo_url} onChange={(v) => setForm((f) => ({ ...f, userinfo_url: v }))} mono />
          <Field label="Scopes (séparés par espaces)" value={form.scopes} onChange={(v) => setForm((f) => ({ ...f, scopes: v }))} placeholder="read:user user:email" mono />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setRegisterOpen(false)}>Annuler</Button>
            <Button size="sm" disabled={!formValid || register.isPending} onClick={() => register.mutate()}>
              {register.isPending ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Dialog — détail (lecture seule, sans secret) */}
      <Dialog open={!!detail} onClose={() => setDetail(null)} title={detail ? `Provider — ${detail.name}` : ""} size="lg">
        {detail && (
          <dl className="space-y-2 text-xs">
            {([
              ["Client ID", detail.client_id],
              ["Secret", detail.client_secret_set ? "●●● défini (jamais renvoyé)" : "non défini"],
              ["Authorize URL", detail.authorize_url],
              ["Token URL", detail.token_url],
              ["Userinfo URL", detail.userinfo_url],
              ["Scopes", detail.scopes.join(", ") || "—"],
              ["Statut", detail.enabled ? "actif" : "inactif"],
            ] as const).map(([k, v]) => (
              <div key={k} className="flex gap-3">
                <dt className="w-32 shrink-0 font-medium text-foreground-secondary">{k}</dt>
                <dd className="min-w-0 break-all font-mono text-foreground-tertiary">{v}</dd>
              </div>
            ))}
          </dl>
        )}
      </Dialog>

      {/* Dialog — confirmation de désactivation */}
      <Dialog open={!!confirmDisable} onClose={() => setConfirmDisable(null)} title="Désactiver le provider ?" size="sm">
        <p className="text-sm text-foreground-secondary">
          Les connexions via « {confirmDisable?.name} » seront refusées. La
          configuration est conservée dans le Core.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => setConfirmDisable(null)}>Annuler</Button>
          <Button
            variant="destructive" size="sm"
            disabled={disable.isPending}
            onClick={() => confirmDisable && disable.mutate(confirmDisable)}
          >
            {disable.isPending ? "Désactivation…" : "Désactiver"}
          </Button>
        </div>
      </Dialog>
    </section>
  );
}

/* ── Export ──────────────────────────────────────────────────────────────── */

/**
 * Administration des fournisseurs d'identité (SCIM / LDAP / OAuth).
 * Aucune logique d'authentification ici : le Core valide, stocke et masque.
 */
export function IdentityProviders() {
  return (
    <div className="space-y-4">
      <ScimSection />
      <LdapSection />
      <OAuthSection />
    </div>
  );
}

                </span>
              </div>
              <Button size="sm" variant="ghost" onClick={() => setDetail(p)}>
                Détail
              </Button>
              {p.enabled && (
                <Button
                  size="sm" variant="ghost" className="text-destructive"
                  onClick={() => setConfirmDisable(p)}
                >
                  Désactiver
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}

              <span className="text-[11px] text-destructive">Échec de l&apos;enregistrement</span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

            Activer le provisionnement SCIM
          </label>
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
              {save.isPending ? "Enregistrement…" : "Enregistrer"}
            </Button>
            {save.isError && (
              <span className="text-[11px] text-destructive">Échec de l&apos;enregistrement</span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

