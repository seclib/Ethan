/**
 * Tests WebUI — gestionnaire de capacités (spec §11).
 *
 * Le client API /v1/components est mocké : ces tests valident le rendu et
 * l'orchestration UI (catalogue, états réels, matrice d'actions, dialogs).
 * La logique métier vit dans ETHAN Core — non simulée ici.
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { CapabilitiesSection } from "@/components/features/settings/components/capabilities-section";
import {
  ConfigureDialog,
  InstallDialog,
  UninstallDialog,
} from "@/components/features/settings/components/capability-dialogs";
import {
  detectComponents,
  installComponent,
  listComponents,
  startComponent,
  stopComponent,
  uninstallComponent,
  getInstallPlan,
  getUninstallPlan,
  type ComponentStatus,
} from "@/lib/api/components";

jest.mock("@/lib/api/components", () => ({
  listComponents: jest.fn(),
  detectComponents: jest.fn(),
  getComponent: jest.fn(),
  getInstallPlan: jest.fn(),
  getUninstallPlan: jest.fn(),
  installComponent: jest.fn(),
  configureComponent: jest.fn(),
  testComponent: jest.fn(),
  enableComponent: jest.fn(),
  disableComponent: jest.fn(),
  startComponent: jest.fn(),
  stopComponent: jest.fn(),
  uninstallComponent: jest.fn(),
  listOperations: jest.fn(),
  getOperation: jest.fn(),
  cancelOperation: jest.fn(),
}));

const mockedDetect = detectComponents as jest.Mock;
const mockedList = listComponents as jest.Mock;
const mockedInstall = installComponent as jest.Mock;
const mockedStart = startComponent as jest.Mock;
const mockedStop = stopComponent as jest.Mock;
const mockedUninstall = uninstallComponent as jest.Mock;
const mockedPlan = getInstallPlan as jest.Mock;
const mockedUninstallPlan = getUninstallPlan as jest.Mock;

function makeComponent(over: Partial<ComponentStatus> = {}): ComponentStatus {
  return {
    id: "qdrant",
    name: "Qdrant Vector Database",
    description: "Base de vecteurs optionnelle (Docker).",
    type: "vector_database",
    version: "1.12",
    backend: "docker",
    state: "NOT_INSTALLED",
    enabled: false,
    installed_version: null,
    last_error: null,
    config_keys: [],
    updated_at: null,
    requires_confirmation: true,
    dependencies: [
      { id: "docker", kind: "system", description: "Docker requis.", optional: false },
    ],
    config_schema: [
      {
        name: "http_port",
        type: "port",
        required: false,
        default: 6333,
        description: "Port HTTP exposé.",
        min_value: 1,
        max_value: 65535,
        choices: null,
      },
      {
        name: "tag",
        type: "string",
        required: false,
        default: "v1.12.0",
        description: "Tag d'image Docker.",
        choices: ["latest", "v1.12.0"],
      },
    ],
    data_resources: [
      { kind: "volume", name: "qdrant_storage", description: "Données vectorielles." },
    ],
    provenance: {
      source: "builtin",
      author: "ETHAN",
      url: "",
      license: "",
      checksum: "",
      signature: "",
    },
    ...over,
  };
}

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  mockedList.mockResolvedValue({ capabilities: [makeComponent()] });
  mockedDetect.mockResolvedValue({ states: {} });
  mockedInstall.mockResolvedValue({ operation_id: "op_1" });
  mockedStart.mockResolvedValue(makeComponent({ state: "READY" }));
  mockedStop.mockResolvedValue(makeComponent({ state: "STOPPED" }));
  mockedUninstall.mockResolvedValue({ operation_id: "op_2", delete_data: false });
  mockedPlan.mockResolvedValue({
    capability_id: "qdrant",
    operation: "install",
    requires_confirmation: true,
    steps: [
      { description: "Vérifier le support", kind: "verify" },
      { description: "Télécharger l'image", kind: "install" },
    ],
  });
  mockedUninstallPlan.mockResolvedValue({
    capability_id: "qdrant",
    operation: "uninstall",
    requires_confirmation: true,
    steps: [{ description: "Arrêter", kind: "stop" }],
  });
});

// ── Catalogue + états (sections 1-2) ──────────────────────────────────────

describe("CapabilitiesSection — catalogue et états", () => {
  it("affiche les composants réels du Core groupés par catégorie", async () => {
    renderWithQuery(<CapabilitiesSection />);
    expect(await screen.findByText("Vector Databases")).toBeInTheDocument();
    expect(await screen.findByText("Qdrant Vector Database")).toBeInTheDocument();
    // état réel du Core — jamais un simple « installé »
    expect(screen.getAllByTestId("component-state")[0]).toHaveTextContent(
      "Not installed",
    );
  });

  it("affiche les dépendances et les données persistantes", async () => {
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByText("Qdrant Vector Database");
    expect(screen.getByText(/Dépend de :/)).toBeInTheDocument();
    expect(screen.getByText(/Données : qdrant_storage/)).toBeInTheDocument();
  });

  it("affiche l'état READY quand le Core le confirme", async () => {
    mockedList.mockResolvedValue({
      capabilities: [makeComponent({ state: "READY", enabled: true })],
    });
    renderWithQuery(<CapabilitiesSection />);
    expect(await screen.findByTestId("component-state")).toHaveTextContent("Ready");
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it(" Rafraîchir relance la détection du Core", async () => {
    renderWithQuery(<CapabilitiesSection />);
    fireEvent.click(await screen.findByRole("button", { name: /Rafraîchir/i }));
    await waitFor(() => expect(mockedDetect).toHaveBeenCalledTimes(1));
  });

  it("révèle la provenance Core (source + auteur + licence) sans rien inventer", async () => {
    mockedList.mockResolvedValue({
      capabilities: [
        makeComponent({
          id: "ollama",
          name: "Ollama",
          type: "provider",
          provenance: {
            source: "official",
            author: "Ollama Inc.",
            url: "https://ollama.com",
            license: "MIT",
            checksum: "",
            signature: "",
          },
        }),
      ],
    });
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByText("Ollama");
    expect(screen.getByTestId("component-provenance")).toHaveTextContent("Officiel");
    // Auteur et licence viennent du Core, pas d'une table locale.
    expect(screen.getByText(/Ollama Inc\. · MIT/)).toBeInTheDocument();
    // Vérifiabilité : la source est dans le titre ; checksum vide → omis.
    expect(screen.getByTestId("component-provenance")).toHaveAttribute(
      "title",
      "Source : https://ollama.com",
    );
  });

  it("type stt_tts : regroupé sous Speech / Transcription (miroir du Core)", async () => {
    mockedList.mockResolvedValue({
      capabilities: [
        makeComponent({
          id: "whisper",
          name: "Whisper",
          type: "stt_tts",
          backend: "python_package",
        }),
      ],
    });
    renderWithQuery(<CapabilitiesSection />);
    expect(await screen.findByText("Speech / Transcription")).toBeInTheDocument();
    expect(screen.getByText("Whisper")).toBeInTheDocument();
  });
});

// ── Matrice d'actions (section 3) ─────────────────────────────────────────

describe("Matrice d'actions selon l'état", () => {
  it("NOT_INSTALLED → [Installer] seul", async () => {
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByText("Qdrant Vector Database");
    expect(screen.getByRole("button", { name: "Installer" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Arrêter" })).not.toBeInTheDocument();
  });

  it("READY → [Arrêter] [Configurer] [Désinstaller]", async () => {
    mockedList.mockResolvedValue({ capabilities: [makeComponent({ state: "READY" })] });
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByTestId("component-state");
    expect(screen.getByRole("button", { name: "Arrêter" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Configurer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Désinstaller" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Installer" })).not.toBeInTheDocument();
  });

  it("READY → clic Arrêter appelle le Core (stop)", async () => {
    mockedList.mockResolvedValue({ capabilities: [makeComponent({ state: "READY" })] });
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByTestId("component-state");
    fireEvent.click(screen.getByRole("button", { name: "Arrêter" }));
    await waitFor(() => expect(mockedStop).toHaveBeenCalledWith("qdrant"));
  });

  it("builtin READY → [Configurer] seul, jamais Install/Start/Stop/Uninstall (spec §8)", async () => {
    mockedList.mockResolvedValue({
      capabilities: [
        makeComponent({
          id: "memory",
          name: "Memory (built-in vector backend)",
          backend: "builtin",
          state: "READY",
        }),
      ],
    });
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByText("Memory (built-in vector backend)");
    expect(screen.getByRole("button", { name: "Configurer" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Installer" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Démarrer" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Arrêter" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Désinstaller" })).not.toBeInTheDocument();
  });

  it("ERROR → [Voir les détails] [Réessayer] + dernière erreur affichée", async () => {
    mockedList.mockResolvedValue({
      capabilities: [
        makeComponent({ state: "ERROR", last_error: "docker pull a échoué" }),
      ],
    });
    renderWithQuery(<CapabilitiesSection />);
    await screen.findByText(/docker pull a échoué/);
    expect(screen.getByRole("button", { name: "Voir les détails" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Réessayer" })).toBeInTheDocument();
  });

  it("INSTALLING → indicateur d'opération, aucune action", async () => {
    mockedList.mockResolvedValue({
      capabilities: [makeComponent({ state: "INSTALLING" })],
    });
    renderWithQuery(<CapabilitiesSection />);
    expect(await screen.findByText(/opération en cours/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Installer" })).not.toBeInTheDocument();
  });
});

// ── Dialogs (sections 4-7) ────────────────────────────────────────────────

describe("InstallDialog", () => {
  it("affiche le plan fourni par le Core avant confirmation", async () => {
    renderWithQuery(
      <InstallDialog
        component={makeComponent()}
        open
        onClose={jest.fn()}
        onCompleted={jest.fn()}
      />,
    );
    expect(await screen.findByText("Vérifier le support")).toBeInTheDocument();
    expect(screen.getByText("Télécharger l'image")).toBeInTheDocument();
    expect(screen.getByText("docker")).toBeInTheDocument(); // dépendance (id exact)
    expect(screen.getByText(/qdrant_storage/)).toBeInTheDocument(); // données
  });

  it("[Installer] lance l'installation via le Core", async () => {
    renderWithQuery(
      <InstallDialog
        component={makeComponent()}
        open
        onClose={jest.fn()}
        onCompleted={jest.fn()}
      />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Installer" }));
    await waitFor(() => expect(mockedInstall).toHaveBeenCalledWith("qdrant"));
  });
});

describe("UninstallDialog — conservation vs suppression des données", () => {
  it("par défaut : conserver les données, pas de double confirmation", async () => {
    const onCompleted = jest.fn();
    renderWithQuery(
      <UninstallDialog
        component={makeComponent({ state: "READY" })}
        open
        onClose={jest.fn()}
        onCompleted={onCompleted}
      />,
    );
    await screen.findByText(/Que faire de ses données/);
    fireEvent.click(screen.getByRole("button", { name: "Désinstaller" }));
    await waitFor(() =>
      expect(mockedUninstall).toHaveBeenCalledWith("qdrant", false),
    );
  });

  it("suppression des données → double confirmation obligatoire", async () => {
    renderWithQuery(
      <UninstallDialog
        component={makeComponent({ state: "READY" })}
        open
        onClose={jest.fn()}
        onCompleted={jest.fn()}
      />,
    );
    await screen.findByText(/Que faire de ses données/);
    fireEvent.click(screen.getByLabelText(/Supprimer définitivement les données/));
    fireEvent.click(screen.getByRole("button", { name: "Désinstaller" }));
    // 1re confirmation : pas d'appel Core encore
    expect(mockedUninstall).not.toHaveBeenCalled();
    // 2e confirmation explicite
    fireEvent.click(
      await screen.findByRole("button", { name: /Supprimer définitivement/ }),
    );
    await waitFor(() => expect(mockedUninstall).toHaveBeenCalledWith("qdrant", true));
  });
});

describe("ConfigureDialog — Guidé / JSON (section 7)", () => {
  it("mode guidé : champs générés depuis le schéma réel du Core", async () => {
    renderWithQuery(
      <ConfigureDialog component={makeComponent()} open onClose={jest.fn()} />,
    );
    await screen.findByText("http_port");
    const port = screen.getByLabelText(/http_port/) as HTMLInputElement;
    expect(port.value).toBe("6333"); // défaut du schéma Core
    const tag = screen.getByLabelText(/tag/) as HTMLSelectElement;
    expect(tag.value).toBe("v1.12.0");
    expect(tag.tagName).toBe("SELECT"); // choices → select guidé
  });

  it("mode JSON : exemple généré du schéma réel, jamais fictif", async () => {
    renderWithQuery(
      <ConfigureDialog component={makeComponent()} open onClose={jest.fn()} />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "JSON" }));
    const textarea = screen.getByLabelText("Configuration JSON") as HTMLTextAreaElement;
    const parsed = JSON.parse(textarea.value);
    expect(parsed).toEqual({ http_port: 6333, tag: "v1.12.0" });
  });

  it("JSON invalide : erreur affichée, pas d'envoi au Core", () => {
    const alertMock = jest.spyOn(window, "alert").mockImplementation(() => {});
    renderWithQuery(
      <ConfigureDialog component={makeComponent()} open onClose={jest.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    const textarea = screen.getByLabelText("Configuration JSON");
    fireEvent.change(textarea, { target: { value: "{ invalid json" } });
    expect(screen.getByRole("alert")).toHaveTextContent(/JSON invalide/);
    alertMock.mockRestore();
  });
});
