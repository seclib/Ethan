import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Skeleton } from "../skeleton";

describe("Skeleton", () => {
  it("renders skeleton element", () => {
    render(<Skeleton />);
    expect(screen.getByRole("generic")).toBeTruthy();
  });
});