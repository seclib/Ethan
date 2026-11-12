import { parseRichContent } from "@/components/features/assistant/rich-response/parse-rich-content";
import { validateChart, validateCallout } from "@/components/features/assistant/rich-response/types";

describe("Rich Response parsing", () => {
  it("garde le Markdown standard", () => {
    const segments = parseRichContent("Texte **important**\n\n- item");
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("markdown");
  });

  it("extrait un bloc code normal", () => {
    const segments = parseRichContent("```ts\nconst x = 1;\n```");
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("code");
    expect(segments[0].language).toBe("ts");
  });

  it("renderise un bloc chart valide", () => {
    const input = "```chart\n{\"type\":\"bar\",\"data\":[{\"label\":\"A\",\"value\":3}]}\n```";
    const segments = parseRichContent(input);
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("rich");
    expect(segments[0].block?.kind).toBe("chart");
  });

  it("retombe sur du code si le JSON est invalide", () => {
    const input = "```chart\n{invalid}\n```";
    const segments = parseRichContent(input);
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("code");
  });

  it("valide les variantes de callout", () => {
    expect(validateCallout({ variant: "success", content: "ok" }).variant).toBe("success");
  });

  it("rejette un graphique sans données", () => {
    expect(() => validateChart({ type: "bar", data: [] })).toThrow();
  });
});
