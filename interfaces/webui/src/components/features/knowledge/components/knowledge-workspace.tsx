"use client";

import * as React from "react";
import { useKnowledge } from "@/components/features/knowledge/hooks/use-knowledge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  Plus,
  Search,
  Trash2,
  FilePlus2,
  FileMinus2,
  Database,
  FileText,
  MoreVertical,
  Pencil,
  X,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function KnowledgeWorkspace() {
  const {
    collections,
    documents,
    isLoading,
    error,
    createCollection,
    deleteCollection,
    updateCollection,
    addDocumentToCollection,
    removeDocumentFromCollection,
    listCollectionDocuments,
    retrieveFromCollection,
    ingestDocument,
  } = useKnowledge();

  // Selection state
  const [selectedCollectionId, setSelectedCollectionId] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState("");
  const [collectionDocs, setCollectionDocs] = React.useState<Record<string, any[]>>({});
  const [loadingDocs, setLoadingDocs] = React.useState(false);

  // Dialogs
  const [createOpen, setCreateOpen] = React.useState(false);
  const [newName, setNewName] = React.useState("");
  const [newDescription, setNewDescription] = React.useState("");
  const [ingestOpen, setIngestOpen] = React.useState(false);
  const [docTitle, setDocTitle] = React.useState("");
  const [docContent, setDocContent] = React.useState("");
  const [renameOpen, setRenameOpen] = React.useState(false);
  const [renameId, setRenameId] = React.useState<string | null>(null);
  const [renameName, setRenameName] = React.useState("");

  // Add document
  const [addDocOpen, setAddDocOpen] = React.useState(false);
  const [selectedDocId, setSelectedDocId] = React.useState("");
  const [addingDoc, setAddingDoc] = React.useState(false);

  // Retrieve
  const [retrieveQuery, setRetrieveQuery] = React.useState("");
  const [retrieveResults, setRetrieveResults] = React.useState<any[]>([]);
  const [retrieving, setRetrieving] = React.useState(false);

  const filteredCollections = collections.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()),
  );

  const selectedCollection = collections.find((c) => c.id === selectedCollectionId) || null;

  // Load documents when a collection is selected
  React.useEffect(() => {
    if (selectedCollectionId) {
      setLoadingDocs(true);
      listCollectionDocuments(selectedCollectionId)
        .then((docs) => setCollectionDocs((prev) => ({ ...prev, [selectedCollectionId]: docs })))
        .catch((err) => console.error("Failed to load docs", err))
        .finally(() => setLoadingDocs(false));
    }
  }, [selectedCollectionId, listCollectionDocuments]);

  const handleCreate = () => {
    if (!newName.trim()) return;
    createCollection(newName.trim(), newDescription.trim());
    setNewName("");
    setNewDescription("");
    setCreateOpen(false);
  };

  const handleIngest = () => {
    if (!docContent.trim()) return;
    ingestDocument({ content: docContent.trim(), title: docTitle.trim() });
    setDocTitle("");
    setDocContent("");
    setIngestOpen(false);
  };

  const handleRename = () => {
    if (!renameId || !renameName.trim()) return;
    updateCollection(renameId, { name: renameName.trim() });
    setRenameOpen(false);
    setRenameId(null);
    setRenameName("");
  };

  const handleAddDocument = async () => {
    if (!selectedCollectionId || !selectedDocId) return;
    setAddingDoc(true);
    try {
      await addDocumentToCollection(selectedCollectionId, selectedDocId);
      const docs = await listCollectionDocuments(selectedCollectionId);
      setCollectionDocs((prev) => ({ ...prev, [selectedCollectionId]: docs }));
      setAddDocOpen(false);
      setSelectedDocId("");
    } catch (err) {
      console.error("Failed to add document", err);
    } finally {
      setAddingDoc(false);
    }
  };

  const handleRemoveDocument = async (documentId: string) => {
    if (!selectedCollectionId) return;
    try {
      await removeDocumentFromCollection(selectedCollectionId, documentId);
      const docs = await listCollectionDocuments(selectedCollectionId);
      setCollectionDocs((prev) => ({ ...prev, [selectedCollectionId]: docs }));
    } catch (err) {
      console.error("Failed to remove document", err);
    }
  };

  const handleRetrieve = async () => {
    if (!selectedCollectionId || !retrieveQuery.trim()) return;
    setRetrieving(true);
    try {
      const results = await retrieveFromCollection(selectedCollectionId, retrieveQuery.trim());
      setRetrieveResults(results);
    } catch (err) {
      console.error("Retrieval failed", err);
    } finally {
      setRetrieving(false);
    }
  };

  return (
    <div className="flex h-full min-h-0">
      {/* Left panel: collections list */}
      <div className="flex w-72 shrink-0 flex-col border-r border-line-1 bg-bg-1/40">
        <div className="flex items-center justify-between border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Knowledge Bases</h2>
          <Button size="sm" variant="primary" onClick={() => setCreateOpen(true)}>
            <Plus className="h-3.5 w-3.5" />
            <span className="ml-1">Nouvelle</span>
          </Button>
        </div>

        <div className="p-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher..."
              className="w-full rounded-lg border border-line-1 bg-bg-1 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {isLoading && (
            <div className="flex items-center justify-center py-8 text-foreground-tertiary">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          )}
          {error && <p className="px-3 py-2 text-xs text-red/80">{error}</p>}
          {filteredCollections.map((collection) => (
            <CollectionRow
              key={collection.id}
              name={collection.name}
              description={collection.description}
              isActive={collection.id === selectedCollectionId}
              onClick={() => setSelectedCollectionId(collection.id)}
              onRename={() => {
                setRenameId(collection.id);
                setRenameName(collection.name);
                setRenameOpen(true);
              }}
              onDelete={() => {
                if (selectedCollectionId === collection.id) setSelectedCollectionId(null);
                deleteCollection(collection.id);
              }}
            />
          ))}
          {filteredCollections.length === 0 && !isLoading && (
            <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">
              Aucune knowledge base
            </p>
          )}
        </div>
      </div>

      {/* Right panel: collection details */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {!selectedCollection ? (
          <div className="flex h-full flex-col items-center justify-center text-center px-4">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
              <Database className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Sélectionnez une knowledge base</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Créez une knowledge base ou sélectionnez-en une pour gérer ses documents, sources et paramètres RAG.
            </p>
            <Button className="mt-4" variant="primary" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              <span className="ml-1">Créer une knowledge base</span>
            </Button>
          </div>
        ) : (
          <div className="p-6">
            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-foreground">{selectedCollection.name}</h1>
                {selectedCollection.description && (
                  <p className="mt-1 text-sm text-muted-foreground">{selectedCollection.description}</p>
                )}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => setIngestOpen(true)}>
                  <FilePlus2 className="h-3.5 w-3.5" />
                  <span className="ml-1">Ingérer</span>
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setAddDocOpen(true)}>
                  <Plus className="h-3.5 w-3.5" />
                  <span className="ml-1">Ajouter doc</span>
                </Button>
              </div>
            </div>

            {/* Documents */}
            <div className="mb-6">
              <h3 className="mb-2 text-sm font-semibold text-foreground-secondary uppercase tracking-wider">
                Documents ({collectionDocs[selectedCollection.id]?.length ?? 0})
              </h3>
              {loadingDocs ? (
                <div className="flex items-center gap-2 py-4 text-sm text-foreground-tertiary">
                  <Loader2 className="h-4 w-4 animate-spin" /> Chargement...
                </div>
              ) : (
                <div className="space-y-1">
                  {(collectionDocs[selectedCollection.id] || []).map((doc) => (
                    <div
                      key={doc.id}
                      className="group flex items-center justify-between gap-2 rounded-lg border border-line-1 bg-bg-1/50 px-3 py-2"
                    >
                      <div className="flex min-w-0 items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-foreground-tertiary" />
                        <span className="truncate text-sm text-foreground-secondary">
                          {doc.title || doc.id.slice(0, 12)}
                        </span>
                      </div>
                      <button
                        onClick={() => handleRemoveDocument(doc.id)}
                        className="shrink-0 rounded p-1 text-foreground-tertiary opacity-0 transition-opacity hover:bg-bg-1 hover:text-red-400 group-hover:opacity-100"
                        title="Retirer"
                      >
                        <FileMinus2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                  {(collectionDocs[selectedCollection.id] || []).length === 0 && (
                    <p className="py-3 text-sm text-foreground-tertiary">
                      Aucun document. Ajoutez des documents à cette knowledge base.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Retrieval */}
            <div>
              <h3 className="mb-2 text-sm font-semibold text-foreground-secondary uppercase tracking-wider">
                Recherche RAG
              </h3>
              <div className="flex gap-2">
                <Input
                  value={retrieveQuery}
                  onChange={(e) => setRetrieveQuery(e.target.value)}
                  placeholder="Rechercher dans la knowledge base..."
                  className="h-9 text-sm"
                  onKeyDown={(e) => e.key === "Enter" && handleRetrieve()}
                />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleRetrieve}
                  disabled={retrieving || !retrieveQuery.trim()}
                >
                  {retrieving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
                  <span className="ml-1">Rechercher</span>
                </Button>
              </div>
              {retrieveResults.length > 0 && (
                <div className="mt-3 space-y-2">
                  {retrieveResults.map((item, idx) => (
                    <div key={idx} className="rounded-lg border border-line-1 bg-bg-1/50 p-3">
                      <p className="text-xs font-medium text-foreground-secondary">{item.document_title}</p>
                      <p className="mt-1 text-sm text-foreground">{item.chunk?.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create collection dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen} title="Nouvelle knowledge base">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Nom</label>
            <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Nom de la knowledge base" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Description</label>
            <Textarea
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="Description optionnelle"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleCreate}>Créer</Button>
          </div>
        </div>
      </Dialog>

      {/* Ingest document dialog */}
      <Dialog open={ingestOpen} onOpenChange={setIngestOpen} title="Ingérer un document dans le RAG">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Titre</label>
            <Input value={docTitle} onChange={(e) => setDocTitle(e.target.value)} placeholder="Titre du document" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Contenu</label>
            <Textarea
              value={docContent}
              onChange={(e) => setDocContent(e.target.value)}
              placeholder="Collez le contenu texte à ingérer..."
              rows={6}
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setIngestOpen(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleIngest}>Ingérer</Button>
          </div>
        </div>
      </Dialog>

      {/* Rename dialog */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen} title="Renommer la knowledge base">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Nom</label>
            <Input value={renameName} onChange={(e) => setRenameName(e.target.value)} placeholder="Nouveau nom" />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setRenameOpen(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleRename}>Renommer</Button>
          </div>
        </div>
      </Dialog>

      {/* Add document dialog */}
      <Dialog open={addDocOpen} onOpenChange={setAddDocOpen} title="Ajouter un document">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Document</label>
            <select
              className="w-full h-10 px-3 text-sm bg-background border border-line-2 rounded-lg text-foreground"
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
            >
              <option value="">Sélectionner un document...</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title || doc.id.slice(0, 12)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setAddDocOpen(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleAddDocument} disabled={addingDoc || !selectedDocId}>
              {addingDoc ? <Loader2 className="h-4 w-4 animate-spin" /> : "Ajouter"}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

interface CollectionRowProps {
  name: string;
  description?: string;
  isActive: boolean;
  onClick: () => void;
  onRename: () => void;
  onDelete: () => void;
}

function CollectionRow({ name, description, isActive, onClick, onRename, onDelete }: CollectionRowProps) {
  const [menuOpen, setMenuOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div
      onClick={onClick}
      className={cn(
        "group flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors",
        isActive ? "bg-bg-3 text-foreground" : "text-foreground-secondary hover:bg-bg-3/60"
      )}
    >
      <Database className="h-4 w-4 shrink-0 text-foreground-tertiary" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{name}</p>
        {description && <p className="truncate text-xs text-foreground-tertiary">{description}</p>}
      </div>
      <div className="relative shrink-0" ref={menuRef}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpen(!menuOpen);
          }}
          className="rounded p-1 text-foreground-tertiary opacity-0 transition-opacity hover:bg-bg-1 group-hover:opacity-100"
          title="Actions"
        >
          <MoreVertical className="h-3.5 w-3.5" />
        </button>
        {menuOpen && (
          <div className="absolute right-0 top-6 z-50 w-40 rounded-lg border border-line-2 bg-surface p-1 shadow-xl">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMenuOpen(false);
                onRename();
              }}
              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-foreground-secondary hover:bg-bg-3 hover:text-foreground"
            >
              <Pencil className="h-3.5 w-3.5" /> Renommer
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMenuOpen(false);
                onDelete();
              }}
              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-red/80 hover:bg-red/10"
            >
              <Trash2 className="h-3.5 w-3.5" /> Supprimer
            </button>
          </div>
        )}
      </div>
    </div>
  );
}