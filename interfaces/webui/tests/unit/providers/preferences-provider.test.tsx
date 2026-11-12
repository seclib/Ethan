/**
 * Rèconciliation des préférences utilisateur avec ETHAN Core.
 *
 * Couvre la règle : le serveur (`GET/PATCH /config/preferences`) est la source
 * de vérité, le `localStorage` (zustand persist) n'est qu'un cache de rendu.
 *
 * - domaine déjà persisté → le serveur écrase le cache local ;
 * - rien d'écrit → le cache local est remonté (première exécution) ;
 * - changement local → PATCH serveur (debounce), jamais de succès silencieux.
 */

import { act, render, waitFor } from "@testing-library/react";

import { apiFetch } from "@/lib/api/client";
import {
  EMPTY_PREFERENCES,
  type UserPreferences,
} from "@/lib/api/preferences";
import { PreferencesProvider } from "@/providers/preferences-provider";
import { useAuth } from "@/providers/auth-provider";
import { useAgentStore } from "@/store/agent.store";
import { useChatModeStore } from "@/store/chat-mode.store";
import { useModelStore } from "@/store/model.store";

jest.mock("@/lib/api/client", () => ({
  apiFetch: jest.fn(),
  ApiError: class ApiError extends Error {},
  streamEvents: jest.fn(),
}));

jest.mock("@/providers/auth-provider", () => ({
  useAuth: jest.fn(),
}));

const mockedApiFetch = apiFetch as unknown as jest.Mock;
const mockedUseAuth = useAuth as unknown as jest.Mock;

const SERVER_PREFERENCES: UserPreferences = {
  ...EMPTY_PREFERENCES,
  active_provider: "ollama",
  active_model: "llama3.1",
  active_agent: "agent-42",
  recent_agents: ["agent-42"],
  chat_mode: "plan",
  reasoning_effort: "high",
};

function routeApiFetch(path: string, options: RequestInit = {}) {
  if (path === "/config/status") {
    return Promise.resolve({ loaded_domains: ["preferences", "rag"] });
  }
  if (path === "/config/preferences") {
    if (options.method === "PATCH") {
      return Promise.resolve({
        ...SERVER_PREFERENCES,
        ...(JSON.parse(String(options.body)) as Partial<UserPreferences>),
      });
    }
    return Promise.resolve(SERVER_PREFERENCES);
  }
  return Promise.reject(new Error(`Unexpected path: ${path}`));
}

function resetStores() {
  useModelStore.setState({ selectedProviderId: "", selectedModel: "" });
  useAgentStore.setState({ selectedAgentId: null, recentAgentIds: [] });
  useChatModeStore.setState({ mode: "act", reasoningEffort: "medium" });
}

function renderProvider() {
  return render(
    <PreferencesProvider>
      <div data-testid="child" />
    </PreferencesProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  resetStores();
  mockedUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false });
});

describe("PreferencesProvider", () => {
  it("le serveur fait autorité quand le domaine est déjà persisté", async () => {
    mockedApiFetch.mockImplementation(routeApiFetch);

    renderProvider();

    await waitFor(() => {
      expect(useModelStore.getState().selectedModel).toBe("llama3.1");
    });

    expect(useModelStore.getState().selectedProviderId).toBe("ollama");
    expect(useAgentStore.getState().selectedAgentId).toBe("agent-42");
    expect(useAgentStore.getState().recentAgentIds).toEqual(["agent-42"]);
    expect(useChatModeStore.getState().mode).toBe("plan");
    expect(useChatModeStore.getState().reasoningEffort).toBe("high");
  });

  it("remonte le cache local quand rien n'a encore été persisté", async () => {
    // Cache local déjà renseigné (session précédente hors-ligne).
    useModelStore.setState({ selectedProviderId: "ollama", selectedModel: "phi3" });
    useChatModeStore.setState({ mode: "debug", reasoningEffort: "low" });

    mockedApiFetch.mockImplementation((path: string, options: RequestInit = {}) => {
      if (path === "/config/status") {
        return Promise.resolve({ loaded_domains: [] });
      }
      if (path === "/config/preferences" && options.method === "PATCH") {
        return Promise.resolve(JSON.parse(String(options.body)));
      }
      return Promise.resolve(EMPTY_PREFERENCES);
    });

    renderProvider();

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/config/preferences",
        expect.objectContaining({ method: "PATCH" }),
      );
    });

    const patchCall = mockedApiFetch.mock.calls.find(
      ([path, options]) =>
        path === "/config/preferences" &&
        (options as RequestInit | undefined)?.method === "PATCH",
    );
    const body = JSON.parse(String((patchCall?.[1] as RequestInit).body));
    expect(body).toMatchObject({ active_model: "phi3", chat_mode: "debug" });

    // Le serveur ne doit PAS avoir écrasé le choix local.
    expect(useModelStore.getState().selectedModel).toBe("phi3");
    expect(useChatModeStore.getState().mode).toBe("debug");
  });

  it("persiste un changement local après hydratation (debounce)", async () => {
    mockedApiFetch.mockImplementation(routeApiFetch);

    renderProvider();

    await waitFor(() => {
      expect(useModelStore.getState().selectedModel).toBe("llama3.1");
    });

    // L'état serveur est la référence : un PATCH identique serait inutile.
    mockedApiFetch.mockClear();

    jest.useFakeTimers();
    try {
      act(() => {
        // Réglage identique à l'état serveur → aucun enregistrement.
        useChatModeStore.getState().setMode("plan");
      });
      act(() => {
        jest.advanceTimersByTime(600);
      });
      expect(
        mockedApiFetch.mock.calls.filter(([path]) => path === "/config/preferences"),
      ).toHaveLength(0);

      act(() => {
        useChatModeStore.getState().setMode("debug");
      });
      act(() => {
        jest.advanceTimersByTime(600);
      });

      const patchCalls = mockedApiFetch.mock.calls.filter(
        ([path, options]) =>
          path === "/config/preferences" &&
          (options as RequestInit | undefined)?.method === "PATCH",
      );
      expect(patchCalls).toHaveLength(1);
      expect(JSON.parse(String((patchCalls[0][1] as RequestInit).body))).toMatchObject({
        chat_mode: "debug",
      });
    } finally {
      jest.useRealTimers();
    }
  });
});
