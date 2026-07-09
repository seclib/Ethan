import { render, screen } from "@testing-library/react";
import { DropdownMenu } from "../dropdown-menu";

describe("DropdownMenu", () => {
  const items = [
    { label: "Edit", onClick: () => {} },
    { label: "Delete", danger: true, onClick: () => {} },
  ];

  it("renders trigger", () => {
    render(<DropdownMenu trigger={<button>Open</button>} items={items} />);
    expect(screen.getByText("Open")).toBeInTheDocument();
  });

  it("opens on click", () => {
    render(<DropdownMenu trigger={<button>Open</button>} items={items} />);
    screen.getByText("Open").click();
    expect(screen.getByText("Edit")).toBeInTheDocument();
  });
});