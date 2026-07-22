import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Switch } from "../switch";

describe("Switch", () => {
  it("renders switch element", () => {
    render(<Switch aria-label="Toggle" />);
    expect(screen.getByRole("switch")).toBeTruthy();
  });
});