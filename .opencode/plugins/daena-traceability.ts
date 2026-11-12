/**
 * DAĒNĀ — traçabilité automatique des interventions OpenCode (P2.8.3).
 *
 * Ce plugin est un **client** : il ne contient aucune logique métier et
 * aucune persistance propre. Il collecte les faits observables d'une
 * intervention (session, fichiers touchés, horodatage) et les transmet à
 * l'API ETHAN, qui les enregistre dans le vault DAĒNĀ via le service Core
 * `core.engineering_memory.traceability`.
 *
 * Mécanisme d'enregistrement :
 *  - `session.idle` → capture automatique d'un rapport d'intervention dès
 *    qu'un tour d'agent a modifié des fichiers ;
 *  - outil `daena_traceability` → enrichissement à la demande par l'agent
 *    (anomalie, dette, transition, tests, rapport complet, contrôle de fin).
 *
 * Contraintes :
 *  - le secret d'authentification n'est **jamais** écrit dans le dépôt : il
 *    vient de l'environnement (`ETHAN_TRACEABILITY_KEY`) ou des options ;
 *  - en cas d'API injoignable, le plugin **ne prétend pas** avoir
 *    enregistré : il journalise l'échec et conserve une trace de secours
 *    locale, rejouable ultérieurement.
 */

type TraceabilityOptions = {
  apiUrl?: string
  apiKey?: string
  enabled?: boolean
  agent?: string
  projectId?: string
  mission?: string
  phase?: string
}

type VcsFileStatus = {
  path?: string
  file?: string
  status?: string
  type?: string
}

type SessionIdleEvent = {
  type?: string
  // OpenCode v2 : la charge utile de l'événement est portée par `data`.
  // `properties` est accepté en repli (compatibilité ascendante).
  data?: {
    sessionID?: string
    info?: { id?: string; title?: string }
    error?: unknown
  }
  properties?: {
    sessionID?: string
    info?: { id?: string; title?: string }
  }
}

type SessionInfo = {
  id?: string
  title?: string
}

const PLUGIN_ID = "daena-traceability"
const DEFAULT_API_URL = "http://127.0.0.1:8000"
const STORAGE_PREFIX = "daena:traceability:"

function log(level: "info" | "error", message: string): void {
  const line = `[${PLUGIN_ID}] ${message}`
  if (level === "error") console.error(line)
  else console.log(line)
}

/**
 * Trace de diagnostic, activable par `ETHAN_TRACEABILITY_DEBUG=1`.
 *
 * Le plugin s'exécute dans le serveur OpenCode : sa sortie standard n'est
 * pas toujours visible dans les journaux du serveur. Une trace fichier
 * explicite rend le diagnostic possible sans bruit permanent.
 */
async function trace(message: string): Promise<void> {
  if (!process.env.ETHAN_TRACEABILITY_DEBUG) return
  try {
    const path = `${process.env.ETHAN_TRACEABILITY_DEBUG_FILE || "/tmp/opencode/daena-traceability.log"}`
    const existing = (await Bun.file(path).exists()) ? await Bun.file(path).text() : ""
    await Bun.write(path, `${existing}${new Date().toISOString()} ${message}\n`)
  } catch {
    // La trace de diagnostic ne doit jamais faire echouer le plugin.
  }
}

function readConfig(options: TraceabilityOptions) {
  const apiUrl = (options.apiUrl || process.env.ETHAN_API_URL || DEFAULT_API_URL).replace(/\/+$/, "")
  const apiKey = options.apiKey || process.env.ETHAN_TRACEABILITY_KEY || ""
  return {
    apiUrl,
    apiKey,
    enabled: options.enabled !== false && apiKey.length > 0,
    agent: options.agent || process.env.ETHAN_TRACEABILITY_AGENT || "opencode",
    projectId: options.projectId || process.env.ETHAN_TRACEABILITY_PROJECT || "",
    mission: options.mission || "",
    phase: options.phase || "",
  }
}

/** Extrait le chemin et l'état d'une entrée `vcs.status()`. */
function normalizeStatus(entry: VcsFileStatus): { path: string; status: string } | null {
  const path = entry.path || entry.file || ""
  if (!path) return null
  const status = (entry.status || entry.type || "modified").toLowerCase()
  return { path, status }
}

/** Signature stable de l'ensemble des fichiers touchés (idempotence). */
function signatureOf(files: { path: string; status: string }[]): string {
  return files
    .map((file) => `${file.status}:${file.path}`)
    .sort()
    .join("|")
}

function buildInterventionId(agent: string, date: Date): string {
  const origin = (agent || "opencode").toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-+|-+$/g, "")
  const pad = (value: number, width = 2) => String(value).padStart(width, "0")
  // Même format que le Core (`build_intervention_id`) :
  // EVT-<AAAAMMJJTHHMMSSffffff>-<ORIGINE>
  const stamp =
    `${date.getUTCFullYear()}${pad(date.getUTCMonth() + 1)}${pad(date.getUTCDate())}` +
    `T${pad(date.getUTCHours())}${pad(date.getUTCMinutes())}${pad(date.getUTCSeconds())}` +
    `${pad(date.getUTCMilliseconds(), 3)}000`
  return `EVT-${stamp}-${origin || "OPENCODE"}`
}

type DaenaContext = {
  options?: TraceabilityOptions
  location?: { directory?: string }
  event: {
    subscribe: (options?: { types?: string[]; signal?: AbortSignal }) => AsyncIterable<SessionIdleEvent>
  }
  vcs: { status: () => Promise<VcsFileStatus[]> }
  storage: {
    get: (key: string) => Promise<unknown>
    set: (key: string, value: unknown) => Promise<void>
  }
  session: {
    get: (input: { sessionID: string }) => Promise<SessionInfo>
  }
  tool: {
    transform: (
      callback: (editor: {
        add: (definition: unknown) => void
      }) => void,
    ) => Promise<unknown>
  }
}

export default {
  id: PLUGIN_ID,

  async setup(ctx: DaenaContext) {
    const config = readConfig(ctx.options || {})

    if (!config.enabled) {
      log(
        "error",
        "désactivé : aucune clé d'API fournie (ETHAN_TRACEABILITY_KEY ou options.apiKey). " +
          "Aucune traçabilité ne sera enregistrée.",
      )
      return () => {}
    }

    log("info", `actif — API ${config.apiUrl}`)
    await trace(`setup — apiUrl=${config.apiUrl} enabled=${config.enabled}`)

    const controller = new AbortController()

    const post = async (path: string, body: unknown): Promise<{ ok: boolean; status: number; body: any }> => {
      const response = await fetch(`${config.apiUrl}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${config.apiKey}`,
        },
        body: JSON.stringify(body),
      })
      let payload: any = null
      try {
        payload = await response.json()
      } catch {
        payload = null
      }
      return { ok: response.ok, status: response.status, body: payload }
    }

    const get = async (path: string): Promise<{ ok: boolean; status: number; body: any }> => {
      const response = await fetch(`${config.apiUrl}${path}`, {
        headers: { Authorization: `Bearer ${config.apiKey}` },
      })
      let payload: any = null
      try {
        payload = await response.json()
      } catch {
        payload = null
      }
      return { ok: response.ok, status: response.status, body: payload }
    }

    /**
     * Outil d'enrichissement : permet a l'agent de consigner dans DAENA les
     * anomalies, dettes, transitions, tests et decisions d'une intervention.
     * La logique metier reste dans le Core (l'API) ; le plugin ne fait que
     * transporter la charge utile.
     */
    await ctx.tool.transform((editor) => {
      editor.add({
        name: "daena_traceability",
        description:
          "Enregistre dans DAENA (mémoire technique ETHAN) les éléments d'une intervention : " +
          "rapport complet, anomalie, dette technique, transition d'anomalie, résultats de tests, " +
          "contrôle de fin d'intervention. Actions : report, anomaly, transition, debt, complete, list.",
        input: {
          type: "object",
          properties: {
            action: {
              type: "string",
              enum: ["report", "anomaly", "transition", "debt", "complete", "list"],
              description: "Opération à effectuer dans DAENA.",
            },
            intervention_id: {
              type: "string",
              description: "Identifiant de l'intervention (obligatoire pour complete).",
            },
            anomaly_id: {
              type: "string",
              description: "Identifiant de l'anomalie (obligatoire pour transition).",
            },
            payload: {
              type: "object",
              description:
                "Contenu de l'enregistrement. Pour un rapport : rubriques A→J (context, work_description, " +
                "files_modified, corrections, anomalies, security_findings, technical_debt, tests, decisions, " +
                "remaining_work, validation_level, nature, mission, phase, project_id...).",
              additionalProperties: true,
            },
          },
          required: ["action"],
          additionalProperties: false,
        },
        execute: async (input: any) => {
          const action = String(input?.action || "")
          const payload = (input?.payload || {}) as Record<string, unknown>
          try {
            if (action === "report") {
              const body = { ...payload, agent: payload.agent || config.agent }
              const result = await post("/v1/memory/traceability/interventions", body)
              return { content: JSON.stringify(result.body ?? { status: result.status }) }
            }
            if (action === "anomaly") {
              const result = await post("/v1/memory/traceability/anomalies", payload)
              return { content: JSON.stringify(result.body ?? { status: result.status }) }
            }
            if (action === "debt") {
              const result = await post("/v1/memory/traceability/debts", payload)
              return { content: JSON.stringify(result.body ?? { status: result.status }) }
            }
            if (action === "transition") {
              const anomalyID = String(input?.anomaly_id || payload.anomaly_id || "")
              if (!anomalyID) return { content: JSON.stringify({ error: "anomaly_id is required" }) }
              const result = await post(`/v1/memory/traceability/anomalies/${encodeURIComponent(anomalyID)}/transition`, payload)
              return { content: JSON.stringify(result.body ?? { status: result.status }) }
            }
            if (action === "complete") {
              const interventionID = String(input?.intervention_id || payload.intervention_id || "")
              if (!interventionID) return { content: JSON.stringify({ error: "intervention_id is required" }) }
              const result = await post(
                `/v1/memory/traceability/interventions/${encodeURIComponent(interventionID)}/complete`,
                {},
              )
              return { content: JSON.stringify(result.body ?? { status: result.status }) }
            }
            if (action === "list") {
              const result = await get("/v1/memory/traceability/interventions?limit=20")
              return { content: JSON.stringify(result.body ?? { status: result.status }) }
            }
            return { content: JSON.stringify({ error: `unknown action: ${action}` }) }
          } catch (error) {
            log("error", `outil daena_traceability en échec : ${(error as Error).message}`)
            return { content: JSON.stringify({ error: (error as Error).message }) }
          }
        },
      })
    })

    /** Trace de secours locale : l'intervention n'est pas perdue si l'API tombe. */
    const writeFallback = async (interventionID: string, body: unknown, reason: string) => {
      try {
        const dir = `${ctx.location?.directory || process.cwd()}/.ethan/traceability-fallback`
        await Bun.write(
          `${dir}/${interventionID}.json`,
          JSON.stringify({ id: interventionID, reason, recorded_at: new Date().toISOString(), body }, null, 2),
        ).catch(async () => {
          const { mkdir } = await import("node:fs/promises")
          await mkdir(dir, { recursive: true })
          await Bun.write(`${dir}/${interventionID}.json`, JSON.stringify({ id: interventionID, reason, body }, null, 2))
        })
        log("error", `API injoignable (${reason}) — trace de secours locale : ${dir}/${interventionID}.json`)
      } catch (error) {
        log("error", `échec d'écriture de la trace de secours : ${(error as Error).message}`)
      }
    }

    const capture = async (event: SessionIdleEvent) => {
      const payload = event.data || event.properties || {}
      const sessionID = payload.sessionID || payload.info?.id
      await trace(`capture — sessionID=${sessionID}`)
      if (!sessionID) return

      const raw = await ctx.vcs.status()
      // `vcs.status()` renvoie `{ location, data }` : la liste des fichiers
      // touchés est dans `data`, chaque entrée portant `file` et `status`.
      const entries = Array.isArray(raw)
        ? raw
        : ((raw as any)?.data ?? (raw as any)?.files ?? (raw as any)?.entries ?? [])
      const files = (entries || []).map(normalizeStatus).filter((item): item is { path: string; status: string } => item !== null)
      await trace(`capture — fichiers touches=${files.length} ${JSON.stringify(files)}`)
      if (files.length === 0) return

      // Idempotence : un même jeu de fichiers ne produit pas deux rapports.
      const signature = signatureOf(files)
      const storageKey = `${STORAGE_PREFIX}${sessionID}`
      const previous = (await ctx.storage.get(storageKey)) as { signature?: string; count?: number } | undefined
      if (previous && previous.signature === signature) return

      let sessionInfo: SessionInfo = {}
      try {
        sessionInfo = (await ctx.session.get({ sessionID })) || {}
      } catch {
        sessionInfo = {}
      }

      const createdAt = new Date().toISOString()
      const interventionID = buildInterventionId(config.agent, new Date(createdAt))
      const modified = files.filter((file) => file.status !== "added").map((file) => file.path)
      const created = files.filter((file) => file.status === "added").map((file) => file.path)
      const failed = event.type === "session.execution.failed"

      const body = {
        intervention_id: interventionID,
        created_at: createdAt,
        project_id: config.projectId || null,
        mission: config.mission,
        phase: config.phase,
        agent: config.agent,
        session_id: sessionID,
        session_title: sessionInfo.title || "",
        nature: "maintenance",
        validation_level: "NOT_VERIFIED",
        context: `Session OpenCode ${sessionInfo.title || sessionID}`,
        work_description: `Tour d'agent terminé ; ${files.length} fichier(s) touché(s) dans l'arbre de travail.`,
        components: [],
        files_created: created,
        files_modified: modified,
        files_deleted: [],
        tests: [],
        tests_not_run: ["Tests non exécutés : la capture automatique ne connaît pas les résultats."],
        validation_limits: [
          "Capture automatique : le contenu du travail n'est pas connu du plugin, seules les modifications de fichiers le sont.",
        ],
        remaining_work: ["Enrichir le rapport (anomalies, tests, décisions) via l'outil daena_traceability."],
        next_steps: ["Appeler l'outil `daena_traceability` avec l'action `report` pour documenter l'intervention."],
        persistent_risks: failed ? ["L'exécution de l'agent s'est terminée en échec."] : [],
      }

      try {
        const result = await post("/v1/memory/traceability/interventions", body)
        if (!result.ok) {
          await writeFallback(interventionID, body, `HTTP ${result.status}`)
          return
        }
        await ctx.storage.set(storageKey, { signature, count: (previous?.count || 0) + 1 })
        log("info", `intervention enregistrée : ${interventionID} (${files.length} fichier(s))`)
      } catch (error) {
        await writeFallback(interventionID, body, (error as Error).message)
      }
    }

    void (async () => {
      try {
        await trace("abonnement session.execution")
        for await (const event of ctx.event.subscribe({
          types: ["session.execution.succeeded", "session.execution.failed"],
          signal: controller.signal,
        })) {
          await trace(`evenement: ${event.type} session=${event.data?.sessionID ?? "?"}`)
          try {
            await capture(event)
          } catch (error) {
            await trace(`capture impossible: ${(error as Error).message}`)
            log("error", `capture impossible : ${(error as Error).message}`)
          }
        }
      } catch (error) {
        await trace(`abonnement interrompu: ${(error as Error).message}`)
        log("error", `abonnement aux événements interrompu : ${(error as Error).message}`)
      }
    })()

    return () => controller.abort()
  },
}
