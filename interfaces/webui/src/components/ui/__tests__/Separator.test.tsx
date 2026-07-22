import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Separator } from "../separator";

describe("Separator", () => {
  it("renders separator element", () => {
    render(<Separator />);
    expect(screen.getByRole("separator")).toBeTruthy();
  });
});