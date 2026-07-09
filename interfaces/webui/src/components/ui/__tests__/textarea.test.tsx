import { render, screen } from "@testing-library/react";
import { Textarea } from "../textarea";

describe("Textarea", () => {
  it("renders with placeholder", () => {
    render(<Textarea placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("shows error message", () => {
    render(<Textarea error="Required" id="test" />);
    expect(screen.getByText("Required")).toBeInTheDocument();
  });

  it("applies success class", () => {
    render(<Textarea success />);
    expect(screen.getByRole("textbox")).toHaveClass("border-success-500");
  });

  it("disables resize when resizable is false", () => {
    render(<Textarea resizable={false} />);
    expect(screen.getByRole("textbox")).toHaveClass("resize-none");
  });
});