import { parseRichContent } from "@/components/features/assistant/rich-response/parse-rich-content";
import { isSafeUrl } from "@/components/features/assistant/rich-response/safe-url";
import { validateChart } from "@/components/features/assistant/rich-response/types";

describe("Rich Response security", () => {
  it("bloque les URL dangereuses", () => {
    expect(isSafeUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeUrl("data:text/html,<script>")).toBe(false);
    expect(isSafeUrl("https://example.com")).toBe(true);
    expect(isSafeUrl("#local")).toBe(true);
  });

  it("ne crée pas de composant pour un type inconnu", () => {
    const input = "```unknown\n{\"payload\":\"x\"}\n```";
    const segments = parseRichContent(input);
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("code");
  });

  it("rejette des données de graphique invalides", () => {
    expect(() => validateChart({ type: "bar", data: [{ label: "A", value: "x" }] })).toThrow();
  });

  it("garde le contenu excessivement volumineux en Markdown sans exécution", () => {
    const input = "# ".repeat(1000) + "Titre";
    const segments = parseRichContent(input);
    expect(segments[0].type).toBe("markdown");
  });
});
