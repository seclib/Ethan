import { render, screen } from "@testing-library/react";
import { AssistantChat } from "../../../src/components/features/assistant/components/assistant-chat";
import type { AssistantMessage } from "../../../src/types/assistant";

/**
 * ÉTAT VIDE du Chat (mode hero) — parité avec l'image de référence :
 * salutation nominative + invite de la section, composer sous la salutation,
 * et AUCUN ancien titre « ETHAN » en doublon.
 *
 * `react-markdown` / `remark-gfm` sont ESM purs : mockés, ils ne participent
 * pas au contrat testé (le rendu markdown est couvert côté message).
 */
jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));
jest.mock("remark-gfm", () => ({ __esModule: true, default: () => {} }));
jest.mock("../../../src/components/shared/logo", () => ({
  LogoSquare: ({ size }: { size?: number }) => (
    <span data-testid="ethan-logo" data-size={size} />
  ),
}));
jest.mock("../../../src/providers/auth-provider", () => ({
  useAuth: () => ({ user: { name: "Seclib" } }),
}));

const userMessage: AssistantMessage = {
  id: "m1",
  role: "user",
  content: "Bonjour",
  timestamp: Date.now(),
};

describe("AssistantChat — état vide (hero)", () => {
  it("affiche la salutation, l'invite de section et le composer", () => {
    render(
      <AssistantChat
        messages={[]}
        onSend={jest.fn()}
        hero
        sectionHint="Rédaction, reformulation, style."
      />,
    );

    expect(screen.getByTestId("ethan-logo")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 })).toBeTruthy();
    expect(screen.getByText("Rédaction, reformulation, style.")).toBeTruthy();
    expect(screen.getByPlaceholderText("Message ETHAN...")).toBeTruthy();
    // Anti-doublon : l'ancien titre « ETHAN » de l'état vide a disparu.
    expect(screen.queryByRole("heading", { name: "ETHAN" })).toBeNull();
  });

  it("hero = bloc non extensible (centré par la page) ; conversation active = pleine hauteur", () => {
    const { container, rerender } = render(
      <AssistantChat messages={[]} onSend={jest.fn()} hero />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).not.toContain("flex-1");

    rerender(<AssistantChat messages={[userMessage]} onSend={jest.fn()} />);
    const activeRoot = container.firstElementChild as HTMLElement;
    expect(activeRoot.className).toContain("flex-1");
    // Le message réel est rendu, plus de salutation.
    expect(screen.queryByTestId("ethan-logo")).toBeNull();
    expect(screen.getByText("Bonjour")).toBeTruthy();
  });

  it("hero ignoré si la conversation n'est pas vierge (sécurité)", () => {
    const { container } = render(
      <AssistantChat messages={[userMessage]} onSend={jest.fn()} hero />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("flex-1");
  });
});