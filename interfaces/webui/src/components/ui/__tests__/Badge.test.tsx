import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Badge } from "../badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>Test</Badge>);
    expect(screen.getByText("Test")).toBeTruthy();
  });
});