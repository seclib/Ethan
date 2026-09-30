/**
 * Tests — Settings → Chat : préférences RÉELLES.
 *
 * Contrat (audit anti-fantôme 2026-09-30) : la section Chat n'expose QUE des
 * contrôles réellement consommés — le store partagé `chat-mode.store`, envoyé
 * au Core dans le payload chat (`mode` / `reasoning_effort`). L'ancien écran
 * fantôme (Default Chat Mode Standard/Creative/Precise, Message History,
 * Auto-save Drafts) ne doit JAMAIS revenir : il n'écrivait rien.
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { ChatSection } from "../../../src/components/features/settings/components/settings-sections";
import { useChatModeStore } from "../../../src/store/chat-mode.store";

describe("Settings → Chat — contrôles réellement consommés", () => {
  beforeEach(() => {
    useChatModeStore.setState({ mode: "act", reasoningEffort: "medium" });
  });

  it("affiche les trois modes réels d'ETHAN Core (Plan / Act / Debug)", () => {
    render(<ChatSection />);

    expect(screen.getByRole("button", { name: /Plan/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Act/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Debug/ })).toBeTruthy();
  });

  it("un clic sur un mode change réellement le store partagé (envoyé au Core)", () => {
    render(<ChatSection />);

    fireEvent.click(screen.getByRole("button", { name: /Debug/ }));

    expect(useChatModeStore.getState().mode).toBe("debug");
    expect(
      screen.getByRole("button", { name: /Debug/ }).getAttribute("aria-pressed"),
    ).toBe("true");
  });

  it("l'effort de raisonnement est persisté dans le même store", () => {
    render(<ChatSection />);

    fireEvent.click(screen.getByRole("button", { name: "High" }));

    expect(useChatModeStore.getState().reasoningEffort).toBe("high");
  });

  it("n'expose aucun contrôle fantôme (Default Model, Temperature, Streaming)", () => {
    render(<ChatSection />);

    expect(screen.queryByText(/Default Model/i)).toBeNull();
    expect(screen.queryByText(/Temperature/i)).toBeNull();
    expect(screen.queryByText(/Max Tokens/i)).toBeNull();
    expect(screen.queryByText(/Streaming/i)).toBeNull();
    expect(screen.queryByText(/Message History/i)).toBeNull();
    expect(screen.queryByText(/Auto-save/i)).toBeNull();
  });
});
