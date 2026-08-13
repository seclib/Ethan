"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ragService, type RagDocument } from "@/core/api/api-client";

export default function DocumentsPage() {
  const [search, setSearch] = React.useState("");
  const [title, setTitle] = React.useState("");
  const [content, setContent] = React.useState("");
  const [documents, setDocuments] = React.useState<RagDocument[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadDocuments = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setDocuments(await ragService.getDocuments());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load documents.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const filteredDocuments = documents.filter((document) => {
    const haystack = `${document.title} ${document.source} ${document.content}`.toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  const handleIngest = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!content.trim()) {
      setError("Document content is required.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const document = await ragService.ingestDocument({ title, content });
      setDocuments((current) => [document, ...current]);
      setTitle("");
      setContent("");
    } catch (ingestError) {
      setError(ingestError instanceof Error ? ingestError.message : "Unable to ingest document.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Documents</h1>
        <p className="mt-2 text-foreground-secondary">Manage files, ingestions, and RAG sources.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ingest a document</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={handleIngest}>
            <Input
              aria-label="Document title"
              placeholder="Document title (optional)"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
            <Textarea
              aria-label="Document content"
              placeholder="Paste text for ETHAN to chunk and index…"
              value={content}
              onChange={(event) => setContent(event.target.value)}
            />
            <Button type="submit" loading={isSubmitting}>Ingest into RAG</Button>
          </form>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Input
          aria-label="Search documents"
          placeholder="Search documents..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Button type="button" variant="outline" onClick={() => void loadDocuments()}>
          Refresh
        </Button>
      </div>

      {error ? <p className="text-sm text-error-600" role="alert">{error}</p> : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <Card><CardContent className="text-sm text-foreground-tertiary">Loading documents…</CardContent></Card>
        ) : filteredDocuments.length ? (
          filteredDocuments.map((document) => (
            <Card key={document.id}>
              <CardHeader>
                <CardTitle>{document.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="line-clamp-3 text-sm text-foreground-secondary">{document.content}</p>
                <p className="text-xs text-foreground-tertiary">
                  {document.chunks.length} chunk{document.chunks.length === 1 ? "" : "s"}
                  {document.source ? ` · ${document.source}` : ""}
                </p>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardHeader><CardTitle>No documents yet</CardTitle></CardHeader>
            <CardContent><p className="text-sm text-foreground-tertiary">Ingest text to make it available to ETHAN&apos;s RAG pipeline.</p></CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
