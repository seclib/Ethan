import { render, screen, fireEvent } from "@testing-library/react";
import { ChatModeToggle } from "../../../src/components/features/assistant/components/chat-mode-toggle";
import { useChatModeStore } from "../../../src/store/chat-mode.store";

/**
 * Plan / Act / Debug sont un RÉGLAGE DU COMPOSER : ils doivent être rendus,
 * cliquables, et leur clic doit réellement changer l'état partagé (envoyé
 * ensuite au Core dans le payload chat — `mode`).
 */
describe("ChatModeToggle — Plan/Act/Debug sous la saisie", () => {
  beforeEach(() => {
    useChatModeStore.setState({ mode: "act" });
  });

  it("rend les TROIS modes + le déclencheur d'effort de raisonnement", () => {
    render(<ChatModeToggle />);

    expect(screen.getByRole("group", { name: "Mode conversationnel" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Plan" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Act" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Debug" })).toBeTruthy();
    expect(screen.getByLabelText("Effort de raisonnement")).toBeTruthy();
  });

  it("un CLIC change réellement le mode (aria-pressed + store partagé)", () => {
    render(<ChatModeToggle />);

    fireEvent.click(screen.getByRole("button", { name: "Debug" }));

    expect(useChatModeStore.getState().mode).toBe("debug");
    expect(
      screen.getByRole("button", { name: "Debug" }).getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      screen.getByRole("button", { name: "Act" }).getAttribute("aria-pressed"),
    ).toBe("false");
  });
});