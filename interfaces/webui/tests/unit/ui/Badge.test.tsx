import { render, screen } from "@testing-library/react";
import { Badge } from "../../../src/components/ui/badge";

describe("Badge", () => {
  it("rend un badge avec le texte", () => {
    render(<Badge>Nouveau</Badge>);
    expect(screen.getByText("Nouveau")).toBeTruthy();
  });
});