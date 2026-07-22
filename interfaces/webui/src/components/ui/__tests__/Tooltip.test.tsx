import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Tooltip } from "../tooltip";

describe("Tooltip", () => {
  it("renders tooltip element", () => {
    render(<Tooltip>Info</Tooltip>);
    expect(screen.getByText("Info")).toBeTruthy();
  });
});