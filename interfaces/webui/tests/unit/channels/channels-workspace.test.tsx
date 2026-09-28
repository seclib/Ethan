import * as React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests de la page Channels (/channels) — contrat d'interface uniquement.
 *
 * Les canaux et leurs messages appartiennent au Core (ChannelStore) : le test
 * ne mocke que le client API (@/lib/api/channels) et vérifie que l'interface
 * affiche exactement ce que le Core renvoie et lui transmet les actions
 * (création, envoi d'un message, suppression) — aucun état métier local.
 */

const mockListChannels = jest.fn();
const mockCreateChannel = jest.fn();
const mockDeleteChannel = jest.fn();
const mockListMessages = jest.fn();
const mockAddMessage = jest.fn();

jest.mock("@/lib/api/channels", () => ({
  listChannels: (...a: unknown[]) => mockListChannels(...a),
  createChannel: (...a: unknown[]) => mockCreateChannel(...a),
  deleteChannel: (...a: unknown[]) => mockDeleteChannel(...a),
  listChannelMessages: (...a: unknown[]) => mockListMessages(...a),
  addChannelMessage: (...a: unknown[]) => mockAddMessage(...a),
}));

const mockAddToast = jest.fn();
jest.mock("@/store/ui.store", () => ({
  useUIStore: (selector?: (s: { addToast: typeof mockAddToast }) => unknown) => {
    const state = { addToast: mockAddToast };
    return selector ? selector(state) : state;
  },
}));

// Imports APRÈS les mocks.
import { ChannelsWorkspace } from "@/components/features/channels/channels-workspace";
import type { Channel, ChannelMessage } from "@/lib/api/channels";

function makeChannel(over: Partial<Channel> = {}): Channel {
  return {
    id: "c1",
    name: "équipe-core",
    description: "canal de test",
    user_id: "fatsio",
    members: ["fatsio"],
    metadata: {},
    created_at: "2026-01-01T09:00:00.000Z",
    updated_at: "2026-01-01T09:00:00.000Z",
    ...over,
  };
}

function makeMessage(over: Partial<ChannelMessage> = {}): ChannelMessage {
  return {
    id: "m1",
    channel_id: "c1",
    role: "user",
    content: "bonjour Core",
    user_id: "fatsio",
    created_at: "2026-01-01T10:00:00.000Z",
    ...over,
  };
}

function renderWorkspace() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChannelsWorkspace />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("ChannelsWorkspace — états honnêtes", () => {
  it("aucun canal : état vide nommant le Core", async () => {
    mockListChannels.mockResolvedValue([]);

    renderWorkspace();

    expect(await screen.findByText(/Aucun canal/)).toBeInTheDocument();
    expect(screen.getByText(/ChannelStore/)).toBeInTheDocument();
  });

  it("erreur Core : message explicite + Réessayer relance", async () => {
    mockListChannels
      .mockRejectedValueOnce(new Error("core indisponible"))
      .mockResolvedValue([]);

    renderWorkspace();

    expect(await screen.findByText("Impossible de charger les canaux")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));

    await waitFor(() => expect(mockListChannels).toHaveBeenCalledTimes(2));
  });

  it("aucun canal sélectionné : invitation à choisir, pas de données inventées", async () => {
    mockListChannels.mockResolvedValue([makeChannel()]);

    renderWorkspace();

    expect(
      await screen.findByText("Sélectionnez un canal pour lire et publier ses messages."),
    ).toBeInTheDocument();
    expect(mockListMessages).not.toHaveBeenCalled();
  });
});

describe("ChannelsWorkspace — fil de messages du Core", () => {
  it("sélection d'un canal : messages réels affichés", async () => {
    mockListChannels.mockResolvedValue([makeChannel()]);
    mockListMessages.mockResolvedValue([makeMessage()]);

    renderWorkspace();

    fireEvent.click(await screen.findByText("équipe-core"));

    expect(await screen.findByText("bonjour Core")).toBeInTheDocument();
    expect(mockListMessages).toHaveBeenCalledWith("c1");
  });

  it("canal sans message : état vide explicite", async () => {
    mockListChannels.mockResolvedValue([makeChannel()]);
    mockListMessages.mockResolvedValue([]);

    renderWorkspace();
    fireEvent.click(await screen.findByText("équipe-core"));

    expect(await screen.findByText("Aucun message dans ce canal.")).toBeInTheDocument();
  });
});

describe("ChannelsWorkspace — écritures arbitrées par le Core", () => {
  it("envoi d'un message : contenu + rôle transmis au Core", async () => {
    mockListChannels.mockResolvedValue([makeChannel()]);
    mockListMessages.mockResolvedValue([]);
    mockAddMessage.mockResolvedValue(makeMessage({ id: "m2", content: "salut" }));

    renderWorkspace();
    fireEvent.click(await screen.findByText("équipe-core"));
    await screen.findByText("Aucun message dans ce canal.");

    fireEvent.change(screen.getByPlaceholderText("Écrire un message…"), {
      target: { value: "salut" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Envoyer/ }));

    await waitFor(() =>
      expect(mockAddMessage).toHaveBeenCalledWith("c1", { content: "salut", role: "user" }),
    );
    expect(screen.getByPlaceholderText("Écrire un message…")).toHaveValue("");
  });

  it("le rôle choisi est transmis au Core", async () => {
    mockListChannels.mockResolvedValue([makeChannel()]);
    mockListMessages.mockResolvedValue([]);
    mockAddMessage.mockResolvedValue(makeMessage({ id: "m3", role: "assistant" }));

    renderWorkspace();
    fireEvent.click(await screen.findByText("équipe-core"));
    await screen.findByText("Aucun message dans ce canal.");

    fireEvent.change(screen.getByLabelText("Rôle du message"), {
      target: { value: "assistant" },
    });
    fireEvent.change(screen.getByPlaceholderText("Écrire un message…"), {
      target: { value: "réponse" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Envoyer/ }));

    await waitFor(() =>
      expect(mockAddMessage).toHaveBeenCalledWith("c1", { content: "réponse", role: "assistant" }),
    );
  });

  it("création d'un canal : POST Core puis sélection du canal créé", async () => {
    mockListChannels
      .mockResolvedValueOnce([])
      .mockResolvedValue([makeChannel({ id: "c9", name: "nouveau" })]);
    mockCreateChannel.mockResolvedValue(makeChannel({ id: "c9", name: "nouveau" }));
    mockListMessages.mockResolvedValue([]);

    renderWorkspace();
    await screen.findByText(/Aucun canal/);

    fireEvent.click(screen.getByTitle("Nouveau canal"));
    fireEvent.change(screen.getByPlaceholderText("ex: équipe-core"), {
      target: { value: "nouveau" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Créer/ }));

    await waitFor(() =>
      expect(mockCreateChannel).toHaveBeenCalledWith({ name: "nouveau", description: "" }),
    );
    await waitFor(() => expect(mockListMessages).toHaveBeenCalledWith("c9"));
  });

  it("suppression confirmée : DELETE Core", async () => {
    mockListChannels.mockResolvedValue([makeChannel()]);
    mockListMessages.mockResolvedValue([]);
    mockDeleteChannel.mockResolvedValue({ status: "deleted" });

    renderWorkspace();
    fireEvent.click(await screen.findByText("équipe-core"));
    await screen.findByText("Aucun message dans ce canal.");

    fireEvent.click(screen.getByRole("button", { name: /Supprimer/ }));
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Supprimer" }));

    await waitFor(() => expect(mockDeleteChannel).toHaveBeenCalledWith("c1"));
  });
});
