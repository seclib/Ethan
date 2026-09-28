/**
 * Tests de contrat — chemins HTTP des clients API du WebUI.
 *
 * Non-régression : ces clients utilisaient `/v1/...` alors que les routeurs
 * FastAPI correspondants ne sont PAS montés sous `/v1`
 * (`interfaces/api/main.py` → `include_router` sans préfixe pour
 * connections / integrations / reminders, et `/files` pour le FileStore).
 * Toute requête partait donc en 404 alors que le Core était fonctionnel.
 *
 * Le proxy Next (`src/app/api/[...path]/route.ts`) retire uniquement le
 * préfixe `/api` : le chemin passé à `apiFetch` doit donc être le chemin
 * backend exact.
 *
 * Convention du repo : seul le client HTTP bas niveau est mocké ; on vérifie
 * ce que le WebUI demande au Core, jamais l'implémentation du Core.
 */

import type { apiFetch as ApiFetchFn } from "@/lib/api/client";

const mockApiFetch = jest.fn(async () => []) as unknown as jest.MockedFunction<
  typeof ApiFetchFn
>;

jest.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...(args as [string])),
}));

/* ── Clients ────────────────────────────────────────────────────────────── */

import { listProviders, listConnections, disconnect } from "@/lib/api/connections";
import {
  listIntegrations,
  getIntegration,
  connectIntegration,
  disconnectIntegration,
  testIntegration,
} from "@/lib/api/integrations";
import {
  listReminders,
  getReminder,
  enableReminder,
  disableReminder,
  fireReminder,
} from "@/lib/api/reminders";
import { listFiles, getFile, deleteFile } from "@/lib/api/files";
import { listImageFiles } from "@/lib/api/library";
import { search, listSearchTypes } from "@/lib/api/search";

/** Chemins backend réellement exposés (extraits de `interfaces/api/main.py`). */
const BACKEND_PATHS = {
  connections: "/connections",
  integrations: "/integrations",
  reminders: "/reminders",
  files: "/files",
  search: "/v1/search",
};

function pathsCalled(): string[] {
  return mockApiFetch.mock.calls.map((call) => String(call[0]));
}

beforeEach(() => {
  mockApiFetch.mockClear();
});

/* ── Connections ────────────────────────────────────────────────────────── */

describe("lib/api/connections — préfixe backend", () => {
  it("appelle /connections (et non /v1/connections)", async () => {
    await listConnections();
    expect(pathsCalled()).toEqual([BACKEND_PATHS.connections]);
  });

  it("appelle le catalogue /connections/providers", async () => {
    await listProviders();
    expect(pathsCalled()).toEqual([`${BACKEND_PATHS.connections}/providers`]);
  });

  it("appelle la suppression /connections/{provider}", async () => {
    await disconnect("github");
    expect(pathsCalled()).toEqual([`${BACKEND_PATHS.connections}/github`]);
    expect(mockApiFetch.mock.calls[0]?.[1]).toMatchObject({ method: "DELETE" });
  });

  it("n'émet jamais de chemin /v1/connections", async () => {
    await listConnections();
    expect(pathsCalled().some((p) => p.startsWith("/v1/connections"))).toBe(false);
  });
});

/* ── Integrations ───────────────────────────────────────────────────────── */

describe("lib/api/integrations — préfixe backend", () => {
  it("appelle /integrations et /integrations/{id}", async () => {
    await listIntegrations();
    await getIntegration("abc");
    expect(pathsCalled()).toEqual([
      BACKEND_PATHS.integrations,
      `${BACKEND_PATHS.integrations}/abc`,
    ]);
  });

  it("appelle les actions de cycle de vie sur /integrations/{id}/*", async () => {
    await connectIntegration("abc");
    await disconnectIntegration("abc");
    await testIntegration("abc");
    expect(pathsCalled()).toEqual([
      `${BACKEND_PATHS.integrations}/abc/connect`,
      `${BACKEND_PATHS.integrations}/abc/disconnect`,
      `${BACKEND_PATHS.integrations}/abc/test`,
    ]);
  });

  it("n'émet jamais de chemin /v1/integrations", async () => {
    await listIntegrations();
    expect(pathsCalled().some((p) => p.startsWith("/v1/integrations"))).toBe(false);
  });
});

/* ── Reminders ──────────────────────────────────────────────────────────── */

describe("lib/api/reminders — préfixe backend", () => {
  it("appelle /reminders et /reminders/{id}", async () => {
    await listReminders();
    await getReminder("r1");
    expect(pathsCalled()).toEqual([
      BACKEND_PATHS.reminders,
      `${BACKEND_PATHS.reminders}/r1`,
    ]);
  });

  it("appelle enable/disable/fire sur /reminders/{id}/*", async () => {
    await enableReminder("r1");
    await disableReminder("r1");
    await fireReminder("r1");
    expect(pathsCalled()).toEqual([
      `${BACKEND_PATHS.reminders}/r1/enable`,
      `${BACKEND_PATHS.reminders}/r1/disable`,
      `${BACKEND_PATHS.reminders}/r1/fire`,
    ]);
  });

  it("n'émet jamais de chemin /v1/reminders", async () => {
    await listReminders();
    expect(pathsCalled().some((p) => p.startsWith("/v1/reminders"))).toBe(false);
  });
});

/* ── Files (Core FileStore) ─────────────────────────────────────────────── */

describe("lib/api/files — préfixe backend", () => {
  it("appelle /files, /files/{id} et /files/{id} en DELETE", async () => {
    await listFiles();
    await getFile("f1");
    await deleteFile("f1");
    expect(pathsCalled()).toEqual([
      BACKEND_PATHS.files,
      `${BACKEND_PATHS.files}/f1`,
      `${BACKEND_PATHS.files}/f1`,
    ]);
  });

  it("ne déclare jamais l'utilisateur propriétaire (identité = JWT)", async () => {
    await listFiles();
    expect(pathsCalled()[0]).not.toContain("user_id");
  });
});

/* ── Library (images = FileStore) ───────────────────────────────────────── */

describe("lib/api/library — images issues du FileStore", () => {
  it("lit /files et mappe les champs du Core (filename/content_type)", async () => {
    mockApiFetch.mockResolvedValueOnce([
      {
        id: "img-1",
        filename: "capture.png",
        content_type: "image/png",
        size: 2048,
        created_at: "2024-01-01T00:00:00Z",
      },
      {
        id: "doc-1",
        filename: "notes.txt",
        content_type: "text/plain",
        size: 10,
        created_at: "2024-01-01T00:00:00Z",
      },
    ] as never);

    const items = await listImageFiles();
    expect(pathsCalled()).toEqual([BACKEND_PATHS.files]);
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({
      id: "img-1",
      title: "capture.png",
      mime_type: "image/png",
      size: 2048,
    });
  });
});

/* ── Search ─────────────────────────────────────────────────────────────── */

describe("lib/api/search — route montée sous /v1", () => {
  it("appelle /v1/search (route bien montée sous /v1)", async () => {
    await search("ethan");
    expect(pathsCalled()[0]).toMatch(/^\/v1\/search\?/);
    expect(pathsCalled()[0]).toContain("q=ethan");
  });

  it("appelle /v1/search/types", async () => {
    await listSearchTypes();
    expect(pathsCalled()).toEqual([`${BACKEND_PATHS.search}/types`]);
  });
});