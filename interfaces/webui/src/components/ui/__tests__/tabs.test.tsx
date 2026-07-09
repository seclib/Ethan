import { render, screen } from "@testing-library/react";
import { Tabs } from "../tabs";

describe("Tabs", () => {
  const items = [
    { value: "tab1", label: "Tab 1", content: <p>Content 1</p> },
    { value: "tab2", label: "Tab 2", content: <p>Content 2</p> },
  ];

  it("renders tabs", () => {
    render(<Tabs items={items} defaultValue="tab1" />);
    expect(screen.getByText("Tab 1")).toBeInTheDocument();
    expect(screen.getByText("Tab 2")).toBeInTheDocument();
  });

  it("shows default tab content", () => {
    render(<Tabs items={items} defaultValue="tab1" />);
    expect(screen.getByText("Content 1")).toBeInTheDocument();
  });
});