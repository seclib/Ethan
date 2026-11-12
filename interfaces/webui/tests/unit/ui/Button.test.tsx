import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../../../src/components/ui/button";

describe("Button", () => {
  it("affiche le texte", () => {
    render(<Button>Cliquez</Button>);
    expect(screen.getByText("Cliquez")).toBeTruthy();
  });

  it("déclenche le onClick", () => {
    let value = false;
    render(<Button onClick={() => { value = true; }}>Envoyer</Button>);
    fireEvent.click(screen.getByText("Envoyer"));
    expect(value).toBe(true);
  });
});