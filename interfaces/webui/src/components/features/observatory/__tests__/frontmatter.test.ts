import { parseFrontmatter } from "../components/frontmatter";

describe("parseFrontmatter", () => {
  it("returns an empty set when there is no frontmatter", () => {
    expect(parseFrontmatter("# Hello\nworld")).toEqual({ values: [] });
  });

  it("parses scalar values", () => {
    const md = '---\nid: "DEC-2026-001"\nstatus: APPROVED\nimpact: high\n---\nbody';
    expect(parseFrontmatter(md).values).toEqual([
      { key: "id", value: "DEC-2026-001" },
      { key: "status", value: "APPROVED" },
      { key: "impact", value: "high" },
    ]);
  });

  it("parses simple lists", () => {
    const md = "---\ncomponents:\n  - CMP-001\n  - CMP-002\n---\nbody";
    expect(parseFrontmatter(md).values).toEqual([
      { key: "components", value: "CMP-001, CMP-002" },
    ]);
  });

  it("strips quotes from quoted scalars", () => {
    const md = "---\ntitle: 'some title'\n---\nbody";
    expect(parseFrontmatter(md).values).toEqual([{ key: "title", value: "some title" }]);
  });
});
