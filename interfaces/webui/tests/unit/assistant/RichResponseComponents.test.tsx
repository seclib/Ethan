import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RichContent } from "@/components/features/assistant/rich-response/rich-content";
import { isSafeHref } from "@/components/features/assistant/rich-response/standard-markdown";

jest.mock("@/components/features/assistant/rich-response/standard-markdown", () => ({
  StandardMarkdown: ({ content }: { content: string }) => <span>{content}</span>,
  isSafeHref: (href?: string) => Boolean(href && !href.toLowerCase().startsWith("javascript:")),
}));

describe("Rich Response components", () => {
  it("affiche le Markdown standard sans corruption", () => {
    const content = "Paragraphe simple";
    render(<RichContent content={content} />);
    expect(screen.getByText(content)).toBeInTheDocument();
  });

  it("rend un callout", () => {
    const input = "```callout\n{\"variant\":\"warning\",\"title\":\"Attention\",\"content\":\"Contenu\"}\n```";
    render(<RichContent content={input} />);
    expect(screen.getByText("Attention")).toBeInTheDocument();
    expect(screen.getByText("Contenu")).toBeInTheDocument();
  });

  it("rend un statut", () => {
    const input = "```status\n{\"status\":\"running\",\"label\":\"Analyse\"}\n```";
    render(<RichContent content={input} />);
    expect(screen.getByText("Analyse")).toBeInTheDocument();
  });

  it("valide les URLs dangereuses", () => {
    expect(isSafeHref("javascript:alert(1)")).toBe(false);
    expect(isSafeHref("https://example.com")).toBe(true);
  });

  it("fallback lisible sur bloc invalide", () => {
    const input = "```chart\n{invalide}\n```";
    render(<RichContent content={input} />);
    expect(screen.getByText(/invalide/i)).toBeInTheDocument();
  });
});
