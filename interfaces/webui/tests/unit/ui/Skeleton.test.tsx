import { render, screen } from "@testing-library/react";
import { Skeleton } from "../../../src/components/ui/skeleton";

describe("Skeleton", () => {
  it("rend sans crash", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel")).toBeTruthy();
  });
});