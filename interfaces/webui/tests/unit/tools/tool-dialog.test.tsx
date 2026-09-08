import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ToolDialog } from "../../../src/components/features/tools/components/tools-workspace";

const noop = () => {};

describe("ToolDialog — création de tool custom", () => {
  it("affiche le titre et désactive Créer sans nom", () => {
    render(<ToolDialog onClose={noop} onCreated={noop} />);
    expect(screen.getByText("Nouveau tool custom")).toBeTruthy();
    const createBtn = screen.getByRole("button", { name: /Créer/ }) as HTMLButtonElement;
    expect(createBtn.disabled).toBe(true);
  });

  it("active Créer avec un nom valide (JSON par défaut : {})", () => {
    render(<ToolDialog onClose={noop} onCreated={noop} />);
    fireEvent.change(screen.getByPlaceholderText("ex: summarize_text"), {
      target: { value: "mon_tool" },
    });
    const createBtn = screen.getByRole("button", { name: /Créer/ }) as HTMLButtonElement;
    expect(createBtn.disabled).toBe(false);
  });

  it("signale un JSON de paramètres invalide et désactive Créer", () => {
    render(<ToolDialog onClose={noop} onCreated={noop} />);
    fireEvent.change(screen.getByPlaceholderText("ex: summarize_text"), {
      target: { value: "mon_tool" },
    });
    fireEvent.change(screen.getByPlaceholderText('{"text": {"type": "string"}}'), {
      target: { value: "not json {" },
    });
    expect(screen.getByText("JSON invalide.")).toBeTruthy();
    const createBtn = screen.getByRole("button", { name: /Créer/ }) as HTMLButtonElement;
    expect(createBtn.disabled).toBe(true);
  });

  it("refuse un JSON non-objet (array) avec un message explicite", () => {
    render(<ToolDialog onClose={noop} onCreated={noop} />);
    fireEvent.change(screen.getByPlaceholderText('{"text": {"type": "string"}}'), {
      target: { value: "[1, 2]" },
    });
    expect(
      screen.getByText("Les paramètres doivent être un objet JSON ({...}).")
    ).toBeTruthy();
  });
});
