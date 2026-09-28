import { render, screen } from "@testing-library/react";

/**
 * Anti-régression : la barre secondaire remplace l'ancienne AssistantTopBar
 * pleine largeur. Elle NE DOIT PAS perdre de contrôle au passage : l'ancienne
 * barre rendait projet + agent + provider + modèle.
 *
 * Les sélecteurs sont remplacés par des sondes (leur logique réseau est testée
 * ailleurs) : ce test vérifie le CÂBLAGE de la barre.
 */
jest.mock("@/components/features/projects/project-selector", () => ({
  ProjectSelector: () => <div data-testid="project-selector" />,
}));
jest.mock("@/components/shared/model-selector", () => ({
  ModelSelector: () => <div data-testid="model-selector" />,
}));
jest.mock("@/components/features/assistant/components/agent-selector", () => ({
  AgentSelector: () => <div data-testid="agent-selector" />,
}));
jest.mock("@/components/features/assistant/components/provider-selector", () => ({
  ProviderSelector: () => <div data-testid="provider-selector" />,
}));

import { ChatSecondaryBar } from "../../../src/components/features/assistant/components/chat-secondary-bar";
import type { SessionMetrics } from "../../../src/types/assistant";

const metrics = { agentStatus: "run" } as unknown as SessionMetrics;

describe("ChatSecondaryBar — barre compacte du Chat", () => {
  it("conserve TOUS les contrôles de l'ancienne top bar : projet, agent, provider, modèle", () => {
    render(
      <ChatSecondaryBar
        title="Nouvelle conversation"
        metrics={metrics}
        agents={[]}
        selectedAgentId={null}
        onSelectAgent={() => {}}
      />,
    );

    expect(screen.getByText("Nouvelle conversation")).toBeTruthy();
    expect(screen.getByTestId("project-selector")).toBeTruthy();
    expect(screen.getByTestId("agent-selector")).toBeTruthy();
    expect(screen.getByTestId("provider-selector")).toBeTruthy();
    expect(screen.getByTestId("model-selector")).toBeTruthy();
  });

  it("expose l'état de l'agent (pastille de statut) sans logique métier", () => {
    render(<ChatSecondaryBar title="T" metrics={metrics} />);
    expect(screen.getByTitle("Agent status: run")).toBeTruthy();
  });

  it("sans handler d'agent, aucun sélecteur d'agent n'est rendu (pas d'état fantôme)", () => {
    render(<ChatSecondaryBar title="T" metrics={metrics} />);
    expect(screen.queryByTestId("agent-selector")).toBeNull();
    // Le scope projet reste disponible (composant autonome, store partagé).
    expect(screen.getByTestId("project-selector")).toBeTruthy();
  });
});