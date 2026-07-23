import { render, screen } from "@testing-library/react";
import { Progress } from "../../../src/components/ui/progress";

describe("Progress", () => {
  it("rend une barre de progression", () => {
    render(<Progress value={50} />);
    const bar = document.querySelector('[role="progressbar"]');
    expect(bar).toBeTruthy();
  });
});