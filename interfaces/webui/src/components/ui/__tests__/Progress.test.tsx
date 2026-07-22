import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Progress } from "../progress";

describe("Progress", () => {
  it("renders with value", () => {
    render(<Progress value={60} />);
    expect(screen.getByRole("progressbar")).toBeTruthy();
  });
});