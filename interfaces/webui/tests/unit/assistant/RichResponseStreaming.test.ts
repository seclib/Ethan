import { parseRichContent } from "@/components/features/assistant/rich-response/parse-rich-content";

describe("Rich Response streaming", () => {
  it("conserve un texte partiel pendant la génération", () => {
    const partial = "Réponse en cours...";
    const segments = parseRichContent(partial);
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("markdown");
    expect(segments[0].value).toBe(partial);
  });

  it("laisse brut un bloc enrichi incomplet", () => {
    const partial = "```chart\n{\"type\":\"bar\",\"data\":[{\"label\":\"A\",\"value\":1";
    const segments = parseRichContent(partial);
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("markdown");
  });

  it("retombe en code si le JSON est incomplet mais le fence est fermé", () => {
    const partial = "```chart\n{\"type\":\"bar\",\"data\":\n```";
    const segments = parseRichContent(partial);
    expect(segments).toHaveLength(1);
    expect(segments[0].type).toBe("code");
  });
});
