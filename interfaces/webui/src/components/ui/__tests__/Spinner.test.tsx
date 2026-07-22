import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Spinner } from "../spinner";

describe("Spinner", () => {
  it("renders spinner element", () => {
    render(<Spinner />);
    expect(screen.getByRole("status")).toBeTruthy();
  });
});