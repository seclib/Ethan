import { rewriteWikilinks } from "../components/wikilinks";

describe("rewriteWikilinks", () => {
  it("rewrites a plain wikilink into an observatory-wikilink URL", () => {
    expect(rewriteWikilinks("See [[MEMORY_DATA_MODEL]] now")).toBe(
      "See [MEMORY_DATA_MODEL](observatory-wikilink:MEMORY_DATA_MODEL) now",
    );
  });

  it("supports the alias form [[target|alias]]", () => {
    expect(rewriteWikilinks("[[Decision Log|the log]]")).toBe(
      "[the log](observatory-wikilink:Decision%20Log)",
    );
  });

  it("encodes the target in the URL", () => {
    expect(rewriteWikilinks("[[a/b c]]")).toBe(
      "[a/b c](observatory-wikilink:a%2Fb%20c)",
    );
  });

  it("leaves regular links untouched", () => {
    const md = "[normal](https://example.com) and `code [[not-a-link]]`";
    expect(rewriteWikilinks(md)).toContain("[normal](https://example.com)");
  });
});
