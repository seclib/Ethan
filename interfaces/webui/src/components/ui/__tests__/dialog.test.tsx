import { render, screen } from "@testing-library/react";
import { Dialog } from "../dialog";

describe("Dialog", () => {
  it("renders when open", () => {
    render(<Dialog open={true} onOpenChange={() => {}} title="Test Dialog"><p>Content</p></Dialog>);
    expect(screen.getByText("Test Dialog")).toBeInTheDocument();
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(<Dialog open={false} onOpenChange={() => {}} title="Test"><p>Content</p></Dialog>);
    expect(screen.queryByText("Content")).not.toBeInTheDocument();
  });

  it("has dialog role and aria-modal", () => {
    render(<Dialog open={true} onOpenChange={() => {}} title="Test"><p>Content</p></Dialog>);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });
});