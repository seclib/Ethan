import { render, screen, fireEvent } from "@testing-library/react";
import { AssistantInput } from "../../../src/components/features/assistant/components/assistant-input";

/**
 * Vérifie le COMPOSER réellement utilisé par le Chat (rôle de la page chat) :
 * - structure : saisie en haut, rangée d'actions (fichiers/capacités) ET
 *   Plan/Act/Debug sur la MÊME ligne (parité image de référence) ;
 * - saisie fonctionnelle à la SOURIS et au CLAVIER ;
 * - import de fichiers : picker natif réel (upload fait par le Core côté page) ;
 * - anti-fantôme : le micro n'existe que si la page fournit la capacité voix.
 */
describe("AssistantInput — composer du Chat", () => {
  it("place la saisie en haut, les actions/fichiers puis Plan/Act/Debug DESSOUS (même carte)", () => {
    render(
      <AssistantInput
        onSend={jest.fn()}
        onAttach={jest.fn()}
        modeSlot={<div data-testid="modes">Plan / Act / Debug</div>}
      />,
    );

    const textarea = screen.getByPlaceholderText("Message ETHAN...");
    const attach = screen.getByTitle("Attach file");
    const modes = screen.getByTestId("modes");

    // Ordre DOM réel : saisie AVANT actions AVANT modes.
    expect(
      textarea.compareDocumentPosition(attach) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      attach.compareDocumentPosition(modes) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    // Les trois vivent dans la MÊME carte composer (donc visuellement sous la saisie).
    const card = textarea.closest(".rounded-2xl") as HTMLElement;
    expect(card).not.toBeNull();
    expect(card.contains(attach)).toBe(true);
    expect(card.contains(modes)).toBe(true);
  });

  it("MÊME RANGÉE : fichiers et Plan/Act/Debug partagent la rangée d'actions, aucune ligne en plus", () => {
    render(
      <AssistantInput
        onSend={jest.fn()}
        onFilesSelected={jest.fn()}
        modeSlot={<div data-testid="modes">Plan / Act / Debug</div>}
      />,
    );

    // Le parent du bouton d'envoi EST la rangée d'actions du composer.
    const row = screen.getByTitle("Send (Enter)").parentElement as HTMLElement;
    expect(row.contains(screen.getByTitle("Attach file"))).toBe(true);
    expect(row.contains(screen.getByTestId("modes"))).toBe(true);

    // Dernier enfant de la carte : plus aucune rangée de modes en dessous.
    const card = screen
      .getByPlaceholderText("Message ETHAN...")
      .closest(".rounded-2xl") as HTMLElement;
    expect(card.lastElementChild).toBe(row);
  });

  it("ANTI-FANTÔME : le micro n'apparaît que si la page fournit un handler (voix = capacité Core)", () => {
    const { rerender } = render(<AssistantInput onSend={jest.fn()} />);
    // Sans capacité voix fournie par la page : aucun bouton micro.
    expect(screen.queryByTitle("Voice input")).toBeNull();

    rerender(<AssistantInput onSend={jest.fn()} onVoice={jest.fn()} />);
    expect(screen.getByTitle("Voice input")).toBeTruthy();
  });

  it("saisie CLAVIER : Enter envoie, Shift+Enter ne l'envoie pas", () => {
    const onSend = jest.fn();
    render(<AssistantInput onSend={onSend} />);
    const textarea = screen.getByPlaceholderText("Message ETHAN...");

    fireEvent.change(textarea, { target: { value: "Bonjour ETHAN" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();

    fireEvent.keyDown(textarea, { key: "Enter" });
    expect(onSend).toHaveBeenCalledWith("Bonjour ETHAN");
  });

  it("saisie SOURIS : le clic sur Send envoie et vide la zone", () => {
    const onSend = jest.fn();
    render(<AssistantInput onSend={onSend} />);
    const textarea = screen.getByPlaceholderText("Message ETHAN...") as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: "Analyse ce document" } });
    fireEvent.click(screen.getByTitle("Send (Enter)"));

    expect(onSend).toHaveBeenCalledWith("Analyse ce document");
    expect(textarea.value).toBe("");
  });

  it("le bouton d'envoi est désactivé tant que la saisie est vide", () => {
    render(<AssistantInput onSend={jest.fn()} />);
    const send = screen.getByTitle("Send (Enter)") as HTMLButtonElement;
    expect(send.disabled).toBe(true);
    fireEvent.change(screen.getByPlaceholderText("Message ETHAN..."), {
      target: { value: "texte" },
    });
    expect((screen.getByTitle("Send (Enter)") as HTMLButtonElement).disabled).toBe(false);
  });

  it("IMPORT DE FICHIERS : le clic ouvre le picker natif et remonte les fichiers (upload Core côté page)", () => {
    const onFilesSelected = jest.fn();
    render(<AssistantInput onSend={jest.fn()} onFilesSelected={onFilesSelected} />);

    const input = screen.getByTestId("chat-file-input") as HTMLInputElement;
    const clickSpy = jest.spyOn(input, "click");

    fireEvent.click(screen.getByTitle("Attach file"));
    expect(clickSpy).toHaveBeenCalledTimes(1);

    const file = new File(["contenu"], "notes.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFilesSelected).toHaveBeenCalledWith([file]);

    clickSpy.mockRestore();
  });

  it("affiche les fichiers joints près des contrôles et permet de les retirer", () => {
    const onRemoveFile = jest.fn();
    render(
      <AssistantInput
        onSend={jest.fn()}
        attachedFiles={[{ id: "f1", name: "rapport.pdf" }]}
        onRemoveFile={onRemoveFile}
      />,
    );

    expect(screen.getByText("rapport.pdf")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Retirer rapport.pdf"));
    expect(onRemoveFile).toHaveBeenCalledWith("f1");
  });

  it("pendant une génération : bouton Stop cliquable (au lieu d'Envoyer)", () => {
    const onStop = jest.fn();
    render(<AssistantInput onSend={jest.fn()} onStop={onStop} disabled />);

    fireEvent.click(screen.getByLabelText("Stop generation"));
    expect(onStop).toHaveBeenCalledTimes(1);
  });
});