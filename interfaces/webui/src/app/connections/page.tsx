"use client";

/**
 * Page Connexions — gestion des comptes/services externes liés à l'utilisateur
 * ETHAN (Email, GitHub, Medium, Notion, et futurs : GitLab, Drive, Slack…).
 *
 * Toutes les opérations passent par les routes /v1/connections de l'API ETHAN
 * (interfaces/api/routers/connections.py), qui délèguent au ConnectionManager
 * Core (core/integrations/connections). Aucune logique métier ici :
 *   - Le catalogue vient du Core (scopes explicites par provider) ;
 *   - Le statut et l'identité diste (login/email) proviennent de `list()` ;
 *   - L'ouverture d'URL d'autorisation se contente d'ouvrir `authorization_url`
 *     dans un nouvel onglet — le callback OAuth revient au Core, JAMAIS ici ;
 *   - Aucun token, `client_secret`, `code` ou `state` ne transite ou est stocké
 *     dans le frontend (règle repo-wide : secrets = Core/Runtime/SecretManager).
 *
 * Les fournisseurs sont découplés de la page → un nouveau provider (GitLab,
 * Drive…) n'ajoute qu'une icône dans le mapping et apparaît automatiquement.
 *
 * Design : surfaces opaques (règle audit transparence), hiérarchie claire —
 * identité ETHAN conservée (logo carré, tokens thématiques).
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listProviders,
  listConnections,
  connect,
  reconnect,
  testConnection,
  getPermissions,
  disconnect,
  type ConnectionCatalog,
  type Connection,
} from "@/lib/api/connections";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import {
  LifeBuoy,
  Search,
  Shield,
  RefreshCw,
  Unplug,
  Power,
  ExternalLink,
  Mail,
  Github,
  BookOpen,
  type LucideIcon,
} from "lucide-react";

/* ── I. Provider icon mapping (extensible : 1 entry = 1 provider) ─────── */

const PROVIDER_ICONS: Record<string, LucideIcon> = {
  email: Mail,
  github: Github,
  medium: BookOpen,
  notion: LifeBuoy,
};

/* ── II. Types vues ───────────────────────────────────────────────────── */

type ConnectionCard = ConnectionCatalog & {
  connection: Connection | null;
};

function StatusPill({ conn }: { conn: Connection | null }) {
  if (!conn || conn.status === "disconnected") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-line-2 px-2 py-0.5 text-[11px] font-medium text-foreground-tertiary">
        <span className="h-1.5 w-1.5 rounded-full bg-foreground-tertiary" />
        Non connecté
      </span>
    );
  }
  const color =
    conn.status === "connected"
      ? "border-green-500/50 text-green-400 bg-green-500/10"
      : "border-amber-500/50 text-amber-400 bg-amber-500/10";
  const label = conn.status === "connected" ? "Connecté" : conn.status;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${color}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

/** Identité diste publique (login/email) — NON sensible → safe à afficher. */
function accountLabel(conn: Connection): string | null {
  const a = conn.account ?? {};
  return (
    (a.login as string) ?? (a.email as string) ?? (a.user as string) ?? null
  );
}

/* ── III. Carte fournisseur ──────────────────────────────────────────── */

function ProviderCard({
  provider,
  onManage,
}: {
  provider: ConnectionCard;
  onManage: (provider: ConnectionCard) => void;
}) {
  const conn = provider.connection;
  const connected = conn?.status === "connected";
  // Résolution directe depuis le mapping statique (jamais créée au rendu).
  const Icon = PROVIDER_ICONS[provider.id] ?? LifeBuoy;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onManage(provider)}
      onKeyDown={(e) => {
        if (e.key === "Enter") onManage(provider);
      }}
      className="group flex cursor-pointer flex-col gap-3 rounded-xl border border-line-1 bg-bg-1 p-4 transition-colors hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <Icon size={20} />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">
              {provider.label}
            </p>
            <p className="text-[11px] text-foreground-tertiary">
              {provider.description || `Connecter ${provider.label} à ETHAN`}
            </p>
          </div>
        </div>
        <StatusPill conn={conn} />
      </div>

      {/* Compte lié : identité diste publique SEULEMENT. */}
      {connected && accountLabel(conn!) && (
        <p className="text-xs text-foreground-secondary">
          Compte : {accountLabel(conn!)}
        </p>
      )}

      {/* Scopes demandés — explicites depuis le catalogue Core. */}
      {provider.scopes.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 text-[10px]">
          {provider.scopes.slice(0, 3).map((s) => (
            <span
              key={s.scope}
              className="rounded bg-elevated px-1.5 py-0.5 text-foreground-tertiary"
            >
              {s.scope}
            </span>
          ))}
          {provider.scopes.length > 3 && (
            <span className="text-foreground-tertiary">
              +{provider.scopes.length - 3}
            </span>
          )}
        </div>
      )}

      <div className="flex items-center gap-1.5">
        <span className="text-[11px] text-foreground-tertiary">
          {connected
            ? "Géré via le bouton ci-dessous"
            : "Cliquez pour Connecter"}
        </span>
      </div>
    </div>
  );
}

/* ── IV. Dialog gestion : aucun token manipulé côté frontend ─────────── */

interface ManageDialogProps {
  provider: ConnectionCard | null;
  open: boolean;
  onClose: () => void;
  onTestConnection: () => void;
  onPermissions: () => void;
  onReconnect: () => void;
  onDisconnect: () => void;
  testing: boolean;
  reconnecting: boolean;
  disconnecting: boolean;
}

function ManageDialog({
  provider,
  open,
  onClose,
  onTestConnection,
  onPermissions,
  onReconnect,
  onDisconnect,
  testing,
  reconnecting,
  disconnecting,
}: ManageDialogProps) {
  if (!provider) return null;
  const conn = provider.connection;
  const managed = conn?.status === "connected";

  return (
    <Dialog open={open} onClose={onClose} title={provider.label}>
      <div className="space-y-4">
        {/* Identité diste publique. */}
        {managed && (
          <div className="flex items-center gap-2.5 rounded-lg border border-line-1 bg-bg-1 px-3 py-2">
            <Shield size={15} className="text-accent" />
            <div>
              <p className="text-xs text-foreground-tertiary">
                Compte connecté
              </p>
              <p className="text-sm font-medium text-foreground">
                {accountLabel(conn) ?? "Identité inconnue"}
              </p>
            </div>
          </div>
        )}

        {/* Scopes demandés. */}
        <div>
          <p className="mb-1.5 text-xs font-medium text-foreground-tertiary">
            Permissions demandées
          </p>
          <div className="flex flex-wrap gap-1">
            {(provider.scopes.length
              ? provider.scopes
              : [
                  {
                    scope: "Aucun scope explicite",
                    summary: "",
                    sensitive: false,
                  },
                ]
            ).map((s) => (
              <span
                key={s.scope}
                className="inline-flex items-center gap-1 rounded-full border border-line-2 bg-elevated px-2 py-0.5 text-[10px] text-foreground-tertiary"
                title={s.summary || s.scope}
              >
                {s.sensitive && <Shield size={9} className="text-amber-400" />}
                {s.scope}
              </span>
            ))}
          </div>
          {managed &&
            conn?.scopes_granted &&
            conn.scopes_granted.length > 0 && (
              <p className="mt-1.5 text-[10px] text-foreground-tertiary">
                Accordés : {conn.scopes_granted.join(", ")}
              </p>
            )}
        </div>

        {/* Actions — aucune ne manipule de token. */}
        <div className="flex flex-col gap-2 pt-2">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={testing || !managed}
              onClick={onTestConnection}
              title={managed ? "Tester la connexion" : "Connectez-vous d'abord"}
            >
              {testing ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-2 border-t-accent" />
              ) : (
                <Power size={13} />
              )}{" "}
              Tester
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={reconnecting}
              onClick={onReconnect}
              title="Reconnecter via OAuth"
            >
              {reconnecting ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-2 border-t-accent" />
              ) : (
                <RefreshCw size={13} />
              )}{" "}
              Reconnecter
            </Button>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!managed}
              onClick={onPermissions}
            >
              <Shield size={13} /> Permissions
            </Button>
            {managed && (
              <Button
                variant="outline"
                size="sm"
                disabled={disconnecting}
                onClick={onDisconnect}
                className="border-red-500/30 text-red-400 hover:bg-red-500/10"
              >
                {disconnecting ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-2 border-t-accent" />
                ) : (
                  <Unplug size={13} />
                )}{" "}
                Déconnecter
              </Button>
            )}
          </div>
        </div>

        <p className="text-[10px] text-foreground-tertiary">
          Aucun token n&apos;est stocké ou affiché dans l&apos;interface.
          L&apos;ouverture de l&apos;autorisation OAuth se fait dans un nouvel
          onglet et revient au Core.
        </p>
      </div>
    </Dialog>
  );
}

/* ── V. Page principale ──────────────────────────────────────────────── */

export default function ConnectionsPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const [search, setSearch] = React.useState("");
  const [manageTarget, setManageTarget] = React.useState<ConnectionCard | null>(
    null,
  );
  const [oauthWindow, setOauthWindow] = React.useState<Window | null>(null);
  /** Timers de polling OAuth — retirés au statut terminal ET au démontage. */
  const pollTimersRef = React.useRef<number[]>([]);
  React.useEffect(
    () => () => {
      pollTimersRef.current.forEach((t) => window.clearInterval(t));
      pollTimersRef.current = [];
    },
    [],
  );

  const {
    data: catalog = [],
    isLoading: isLoadingCatalog,
    error: catalogError,
  } = useQuery({
    queryKey: ["connections", "providers"],
    queryFn: listProviders,
    retry: false,
  });

  const {
    data: userConnections = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["connections", "mine"],
    queryFn: listConnections,
  });

  const isLoadingView = isLoadingCatalog || isLoading;
  const errorView = catalogError ?? error;

  const cards: ConnectionCard[] = catalog.map((p) => ({
    ...p,
    connection: userConnections.find((c) => c.provider === p.id) ?? null,
  }));

  const filtered =
    search.trim().length === 0
      ? cards
      : cards.filter((c) => {
          const q = search.toLowerCase();
          return (
            c.label.toLowerCase().includes(q) ||
            c.description.toLowerCase().includes(q) ||
            c.scopes.some((s) => s.scope.toLowerCase().includes(q))
          );
        });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["connections"] });
  };

  const toastErr = (e: unknown) =>
    addToast({
      type: "error",
      message: e instanceof Error ? e.message : "Erreur",
    });

  const startFlow = (
    providerId: string,
    fn: typeof connect | typeof reconnect,
  ) => {
    const card = cards.find((c) => c.id === providerId);
    if (!card) return;
    const verb =
      card.connection?.status === "connected" ? "Reconnexion" : "Connexion";
    void fn(providerId)
      .then((res) => {
        const w = window.open(
          res.authorization_url,
          "_blank",
          "noopener,noreferrer",
        );
        setOauthWindow(w);
        addToast({
          type: "info",
          message: `${verb} ${card.label} — validez dans l'onglet ouvert.`,
        });
        // Poll : lit l'état FRAIS depuis le Core (jamais la closure
        // `userConnections` du rendu courant, périmée dès la première
        // invalidation). Le timer est retiré au statut terminal et nettoyé
        // au démontage (aucune fuite d'intervalle).
        const timer = window.setInterval(() => {
          void listConnections()
            .then((fresh) => {
              const conn = fresh.find((c) => c.provider === providerId);
              if (
                !conn ||
                (conn.status !== "connected" && conn.status !== "error")
              ) {
                return; // en attente : on continue de scruter
              }
              window.clearInterval(timer);
              pollTimersRef.current = pollTimersRef.current.filter(
                (t) => t !== timer,
              );
              addToast(
                conn.status === "connected"
                  ? { type: "success", message: `${card.label} connecté` }
                  : {
                      type: "error",
                      message: `${card.label} : connexion échouée`,
                    },
              );
              invalidate();
            })
            .catch(() => {
              /* erreur réseau passagère : on continue de scruter */
            });
        }, 2000);
        pollTimersRef.current.push(timer);
      })
      .catch(toastErr);
  };

  const testMutation = useMutation({
    mutationFn: testConnection,
    onSuccess: (updated: Connection) => {
      addToast({
        type: "success",
        message: `${updated.provider} : test OK — ${updated.account?.login ?? "connecté"}`,
      });
      invalidate();
    },
    onError: (e: unknown) => {
      addToast({
        type: "error",
        message: e instanceof Error ? e.message : "Test échoué",
      });
      invalidate();
    },
  });
  const reconnectMutation = useMutation({
    mutationFn: reconnect,
    onSuccess: (res) => {
      const w = window.open(
        res.authorization_url,
        "_blank",
        "noopener,noreferrer",
      );
      setOauthWindow(w);
    },
    onError: toastErr,
  });
  const disconnectMutation = useMutation({
    mutationFn: disconnect,
    onSuccess: () => {
      addToast({ type: "success", message: "Connexion supprimée" });
      invalidate();
    },
    onError: toastErr,
  });

  React.useEffect(() => {
    return () => {
      if (oauthWindow && !oauthWindow.closed) {
        try {
          oauthWindow.close();
        } catch {
          /* cross-origin guard */
        }
      }
    };
  }, [oauthWindow]);

  // L'en-tête reste rendu pendant le chargement et en cas d'erreur (le
  // spinner n'efface plus l'identité de la page — défaut UX corrigé).
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-6">
        {/* Header. */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
              <LifeBuoy size={18} />
            </span>
            <div>
              <h1 className="text-lg font-semibold text-foreground">
                Connexions externes
              </h1>
              <p className="text-xs text-foreground-tertiary">
                Services liés à votre compte ETHAN — OAuth géré par le Core,
                aucun token dans l&apos;interface
              </p>
            </div>
          </div>
          <div className="relative w-full max-w-xs">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filtrer par service ou scope..."
              className="w-full pl-8 text-sm"
              aria-label="Filtrer les connexions"
            />
          </div>
        </div>

        {/* Contenu : chargement, erreur, vide ou grille — l'en-tête (identité
            de la page) reste TOUJOURS visible pendant le chargement. */}
        {isLoadingView ? (
          <div
            className="mt-16 flex justify-center"
            role="status"
            aria-label="Chargement des connexions"
          >
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-2 border-t-accent" />
          </div>
        ) : errorView ? (
          <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            Impossible de charger les connexions :{" "}
            {errorView instanceof Error ? errorView.message : "erreur"}
          </div>
        ) : filtered.length === 0 ? (
          <div className="mt-8 rounded-xl border border-line-1 bg-bg-1 px-4 py-10 text-center">
            <LifeBuoy
              size={32}
              className="mx-auto mb-2 text-foreground-tertiary"
            />
            <p className="text-sm text-foreground-secondary">
              {catalog.length === 0
                ? "Aucun connecteur disponible"
                : `Aucune connexion ne correspond à « ${search} »`}
            </p>
            {catalog.length > 0 && (
              <p className="mt-1 text-xs text-foreground-tertiary">
                Connectez vos services externes pour les exploiter depuis le
                Chat, Knowledge, Skills et Missions.
              </p>
            )}
          </div>
        ) : (
          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((c) => (
              <ProviderCard
                key={c.id}
                provider={c}
                onManage={() => setManageTarget(c)}
              />
            ))}
          </div>
        )}

        {/* Dialog de gestion (connexion existante). */}
        {manageTarget && manageTarget.connection && (
          <ManageDialog
            provider={manageTarget}
            open
            onClose={() => setManageTarget(null)}
            onTestConnection={() => void testMutation.mutate(manageTarget.id)}
            onPermissions={async () => {
              try {
                const res = await getPermissions(manageTarget.id);
                const granted = res.granted.join(", ") || "aucune";
                const requested =
                  (res.requested ?? []).map((s) => s.scope).join(", ") ||
                  "aucune";
                addToast({
                  type: "info",
                  message: `Permissions demandées : ${requested}. Accordées : ${granted}.`,
                });
              } catch (e) {
                toastErr(e);
              }
            }}
            onReconnect={() => startFlow(manageTarget.id, reconnect)}
            onDisconnect={() => void disconnectMutation.mutate(manageTarget.id)}
            testing={testMutation.isPending}
            reconnecting={reconnectMutation.isPending}
            disconnecting={disconnectMutation.isPending}
          />
        )}

        {/* Dialog de connexion (pas de connexion existante). */}
        {manageTarget && !manageTarget.connection && (
          <Dialog
            open
            onClose={() => setManageTarget(null)}
            title={`Connecter ${manageTarget.label}`}
          >
            <div className="space-y-3">
              <p className="text-sm text-foreground-secondary">
                Vous allez être redirigé·e vers {manageTarget.label} pour
                autoriser ETHAN. Aucun token n&apos;est manipulé ici.
              </p>
              <Button
                size="sm"
                onClick={() => startFlow(manageTarget.id, connect)}
              >
                <ExternalLink size={13} /> Ouvrir l&apos;autorisation OAuth
              </Button>
            </div>
          </Dialog>
        )}
      </div>
    </div>
  );
}
