import React from "react";
import { render, screen } from "@testing-library/react";
import { Button } from "../button";

describe("Button", () => {
  it("renders button content", () => {
    render(<Button>Click</Button>);
    expect(screen.getByRole("button")).toBeInTheDocument();
    expect(screen.getByText("Click")).toBeInTheDocument();
  });
});