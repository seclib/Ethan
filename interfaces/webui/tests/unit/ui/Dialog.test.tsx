import { render, screen, fireEvent, act } from "@testing-library/react";
import * as React from "react";
import { Dialog } from "@/components/ui/dialog";

/**
 * Régression — audit input/focus.
 *
 * Symptôme : impossible de taper plus d'un caractère dans un champ d'un Dialog
 * (création Project, formulaires Settings/Providers...) lorsque le parent
 * passe un callback `onClose` inline (recréé à chaque render).
 *
 * Cause : l'effet focus-trap de Dialog dépendait de `handleClose`
 * (recréé à chaque render via useCallback([onClose, onOpenChange])) →
 * l'effet se ré-exécutait à chaque frappe → dialogRef.focus() volait le
 * focus de l'input en cours de saisie.
 *
 * Fix : l'effet ne dépend plus que de `open`.
 */

function Host({ onClose }: { onClose: () => void }) {
  const [name, setName] = React.useState("");
  return (
    <Dialog open onClose={onClose} title="Create Project">
      <input
        aria-label="Project name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
    </Dialog>
  );
}

describe("Dialog — focus stability (audit input/focus)", () => {
  it("keeps focus on the input while typing, even with an unstable onClose", () => {
    const onClose = jest.fn();
    render(<Host onClose={onClose} />);

    const input = screen.getByLabelText("Project name");
    input.focus();
    expect(document.activeElement).toBe(input);

    // Simule la frappe de plusieurs caractères : chaque frappe recrée le
    // callback `onClose` inline du parent (nouvelle prop → nouveau render).
    for (const ch of ["T", "e", "s", "t"]) {
      act(() => {
        fireEvent.change(input, { target: { value: input.value + ch } });
      });
      // Le focus ne doit JAMAIS quitter l'input pendant la saisie.
      expect(document.activeElement).toBe(input);
    }

    expect(input).toHaveValue("Test");
  });

  it("focuses the dialog panel on open when no child holds focus", () => {
    const { container } = render(
      <Dialog open title="Test">
        <p>content</p>
      </Dialog>,
    );
    const panel = container.querySelector(".modal-content") as HTMLElement;
    expect(document.activeElement).toBe(panel);
  });

  it("preserves a child autoFocus over the panel focus", () => {
    function AutoFocusChild() {
      return (
        <Dialog open title="Confirm">
          <button autoFocus>Confirmer</button>
        </Dialog>
      );
    }
    const { container } = render(<AutoFocusChild />);
    const btn = screen.getByRole("button", { name: /confirmer/i });
    // L'autoFocus du bouton ne doit pas être écrasé par le focus du panel.
    expect(document.activeElement).toBe(btn);
    expect(container.querySelector(".modal-content")).not.toBe(
      document.activeElement,
    );
  });

  it("restores focus to the previously focused element on close", () => {
    function Toggleable() {
      const [open, setOpen] = React.useState(true);
      return (
        <>
          <button onClick={() => setOpen(true)}>Reopen</button>
          <Dialog
            open={open}
            onClose={() => setOpen(false)}
            onOpenChange={setOpen}
            title="Test"
          >
            <button onClick={() => setOpen(false)}>Close inside</button>
          </Dialog>
        </>
      );
    }
    render(<Toggleable />);
    const reopen = screen.getByRole("button", { name: /reopen/i });
    reopen.focus();
    expect(document.activeElement).toBe(reopen);

    fireEvent.click(screen.getByRole("button", { name: /close inside/i }));
    // À la fermeture, le focus revient sur l'élément qui avait le focus avant.
    expect(document.activeElement).toBe(reopen);
  });
});