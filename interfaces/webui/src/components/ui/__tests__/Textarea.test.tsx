import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Textarea } from "../textarea";

describe("Textarea", () => {
  it("renders textarea element", () => {
    render(<Textarea placeholder="Write..." />);
    expect(screen.getByPlaceholderText("Write...")).toBeTruthy();
  });
});