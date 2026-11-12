import { layoutGraph } from "../graph/layout";

const nodes = [
  { id: "a.md", label: "a", path: "a.md" },
  { id: "b.md", label: "b", path: "b.md" },
  { id: "c.md", label: "c", path: "c.md" },
];

const edges = [
  { source: "a.md", target: "b.md" },
];

describe("layoutGraph", () => {
  it("returns a positioned node per input node", () => {
    const { nodes: laidOut } = layoutGraph(nodes, edges, 900, 620);
    expect(laidOut).toHaveLength(3);
    for (const node of laidOut) {
      expect(Number.isFinite(node.x)).toBe(true);
      expect(Number.isFinite(node.y)).toBe(true);
    }
  });

  it("is deterministic for the same inputs", () => {
    const first = layoutGraph(nodes, edges, 900, 620);
    const second = layoutGraph(nodes, edges, 900, 620);
    expect(first.nodes.map((n) => n.x)).toEqual(second.nodes.map((n) => n.x));
    expect(first.nodes.map((n) => n.y)).toEqual(second.nodes.map((n) => n.y));
  });

  it("drops edges referencing unknown nodes without crashing", () => {
    const { nodes: laidOut } = layoutGraph(
      nodes,
      [...edges, { source: "a.md", target: "ghost.md" }],
      900,
      620,
    );
    expect(laidOut).toHaveLength(3);
  });
});
