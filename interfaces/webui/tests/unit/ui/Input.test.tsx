import { render, screen, fireEvent } from "@testing-library/react";
import { Input } from "../../../src/components/ui/input";

describe("Input", () => {
  it("affiche le placeholder", () => {
    render(<Input placeholder="Rechercher" />);
    expect(screen.getByPlaceholderText("Rechercher")).toBeTruthy();
  });

  it("déclenche onChange", () => {
    let value = "";
    render(<Input onChange={(e) => { value = e.target.value; }} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "test" } });
    expect(value).toBe("test");
  });
});