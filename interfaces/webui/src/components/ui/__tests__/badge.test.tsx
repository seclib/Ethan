import { render, screen } from "@testing-library/react";
import { Badge } from "../badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>Test</Badge>);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("applies variant class", () => {
    render(<Badge variant="primary">Primary</Badge>);
    const badge = screen.getByText("Primary");
    expect(badge.className).toContain("bg-accent-600");
  });

  it("renders dot when provided", () => {
    render(<Badge dot>Active</Badge>);
    const badge = screen.getByText("Active");
    expect(badge.querySelector(".w-1\\.5\\.h-1\\.5")).toBeInTheDocument();
  });

  it("applies size class", () => {
    render(<Badge size="sm">Small</Badge>);
    const badge = screen.getByText("Small");
    expect(badge.className).toContain("text-xs");
  });
});