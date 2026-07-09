import { render, screen } from "@testing-library/react";
import { Input } from "../input";

describe("Input", () => {
  it("renders with placeholder", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("applies error state", () => {
    render(<Input error="Required field" id="test" />);
    expect(screen.getByText("Required field")).toBeInTheDocument();
  });

  it("applies success state", () => {
    render(<Input success />);
    expect(screen.getByRole("textbox")).toHaveClass("border-success-500");
  });

  it("is disabled when disabled prop is true", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});