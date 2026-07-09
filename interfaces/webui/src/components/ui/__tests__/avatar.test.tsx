import { render, screen } from "@testing-library/react";
import { Avatar } from "../avatar";

describe("Avatar", () => {
  it("renders fallback text", () => {
    render(<Avatar fallback="JD" />);
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("renders initials from full name", () => {
    render(<Avatar fallback="John Doe" />);
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("renders question mark when no fallback", () => {
    render(<Avatar />);
    expect(screen.getByText("?")).toBeInTheDocument();
  });

  it("applies size class", () => {
    render(<Avatar size="lg" fallback="LG" />);
    expect(screen.getByText("LG")).toHaveClass("w-12", "h-12");
  });
});