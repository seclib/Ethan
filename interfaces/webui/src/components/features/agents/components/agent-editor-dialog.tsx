"use client";

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useCreateAgent, useUpdateAgent, useAgent } from "@/components/features/agents/hooks/use-agents";
import { useQuery } from "@tanstack/react-query";
import { listProviders, type Provider } from "@/lib/api/providers";
import { listSkills, type Skill } from "@/lib/api/skills";
import { listCollectionTree, listKnowledge, type KnowledgeCollectionTree, type KnowledgeNode } from "@/lib/api/knowledge";
import { listFolderTree, type FolderTree } from "@/lib/api/folders";
import { listTools, type CoreTool } from "@/lib/api/tools";
import { X, Plus, Cpu } from "lucide-react";
import type { Agent } from "@/types";

interface AgentEditorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId?: string | null;
}

export function AgentEditorDialog({ open, onOpenChange, agentId }: AgentEditorDialogProps) {
  const { agent, isLoading: isFetching } = useAgent(agentId || null);
  const { mutate: createAgent, isLoading: isCreating } = useCreateAgent();
  const { mutate: updateAgent, isLoading: isUpdating } = useUpdateAgent();
  
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [capabilities, setCapabilities] = React.useState<string[]>([]);
  const [capabilityInput, setCapabilityInput] = React.useState("");
  const [model, setModel] = React.useState("");
  const [provider, setProvider] = React.useState("");
  const [skillIds, setSkillIds] = React.useState<string[]>([]);
  const [collectionIds, setCollectionIds] = React.useState<string[]>([]);
  const [knowledgeNodeIds, setKnowledgeNodeIds] = React.useState<string[]>([]);
  const [toolIds, setToolIds] = React.useState<string[]>([]);
  const [folderIds, setFolderIds] = React.useState<string[]>([]);

  const { data: providers = [] } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => listProviders(),
  });
  const { data: skills = [] } = useQuery<Skill[]>({
    queryKey: ["skills"],
    queryFn: () => listSkills(),
  });
  const { data: collectionTree = [] } = useQuery<KnowledgeCollectionTree[]>({
    queryKey: ["knowledge-collections-tree"],
    queryFn: () => listCollectionTree(),
  });
  const { data: tools = [] } = useQuery<CoreTool[]>({
    queryKey: ["tools"],
    queryFn: () => listTools(),
  });
  const { data: knowledgeNodes = [] } = useQuery<KnowledgeNode[]>({
    queryKey: ["knowledgeNodes"],
    queryFn: () => listKnowledge(),
  });
  const { data: folderTree = [] } = useQuery<FolderTree[]>({
    queryKey: ["folder-tree"],
    queryFn: () => listFolderTree(),
  });

  // Outils builtin/custom vs tools exposés par des serveurs MCP (affichage
  // groupé uniquement — la sélection reste au niveau tool, aucune duplication).
  const coreToolList = tools.filter(
    (t) => !t.provider || t.provider === "builtin" || t.provider === "custom",
  );
  const mcpToolList = tools.filter((t) => !coreToolList.includes(t));
  const mcpGroups = Array.from(
    mcpToolList.reduce((acc, t) => {
      const key = t.provider || "mcp";
      if (!acc.has(key)) acc.set(key, [] as CoreTool[]);
      acc.get(key)!.push(t);
      return acc;
    }, new Map<string, CoreTool[]>()),
  );

  /** Aplatissement de l'arborescence de dossiers (toutes profondeurs). */
  const flatFolders = React.useMemo(() => {
    const walk = (nodes: FolderTree[]): FolderTree[] =>
      nodes.flatMap((n) => [n, ...walk(n.children)]);
    return walk(folderTree);
  }, [folderTree]);
  const selectedFolders = flatFolders.filter((f) => folderIds.includes(f.id));

  const isEditing = !!agentId;
  const isLoading = isCreating || isUpdating;

  // Populate form when agent data is loaded
  React.useEffect(() => {
    if (agent && isEditing) {
      setName(agent.name || "");
      setDescription(agent.description || "");
      setCapabilities(agent.capabilities || []);
      setModel(agent.model || "");
      setProvider(agent.provider || "");
      setSkillIds(agent.skill_ids || []);
      setCollectionIds(
        (agent.knowledge_collection_ids as string[]) ||
          (agent.metadata?.knowledge_ids as string[]) ||
          [],
      );
      setKnowledgeNodeIds(agent.knowledge_ids || []);
      setToolIds(agent.tool_ids || (agent.metadata?.tool_ids as string[]) || []);
      setFolderIds(agent.folder_ids || []);
    } else if (!isEditing) {
      // Reset form on new
      setName("");
      setDescription("");
      setCapabilities([]);
      setModel("");
      setProvider("");
      setSkillIds([]);
      setCollectionIds([]);
      setKnowledgeNodeIds([]);
      setToolIds([]);
      setFolderIds([]);
    }
  }, [agent, isEditing]);

  const handleAddCapability = () => {
    const val = capabilityInput.trim().toLowerCase();
    if (val && !capabilities.includes(val)) {
      setCapabilities([...capabilities, val]);
      setCapabilityInput("");
    }
  };

  const handleRemoveCapability = (cap: string) => {
    setCapabilities(capabilities.filter(c => c !== cap));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      if (isEditing && agentId) {
        await updateAgent(agentId, {
          name,
          description,
          capabilities,
          model: model || undefined,
          provider: provider || undefined,
          skill_ids: skillIds,
          knowledge_collection_ids: collectionIds,
          knowledge_ids: knowledgeNodeIds,
          tool_ids: toolIds,
          folder_ids: folderIds,
        });
      } else {
        await createAgent({
          name,
          description,
          capabilities,
          model: model || undefined,
          provider: provider || undefined,
          skill_ids: skillIds,
          knowledge_collection_ids: collectionIds,
          knowledge_ids: knowledgeNodeIds,
          tool_ids: toolIds,
          folder_ids: folderIds,
        });
      }
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to save agent", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} size="md" title={isEditing ? "Edit Cognitive Agent" : "Deploy New Agent"}>
      <form onSubmit={handleSubmit} className="space-y-6">
        {isFetching ? (
          <div className="flex flex-col items-center justify-center py-10">
            <Cpu size={32} className="animate-pulse text-muted-foreground/50 mb-4" />
            <p className="text-sm text-muted-foreground">Loading agent core...</p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Designation <span className="text-destructive">*</span>
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Data Analyst"
                  className="bg-elevated border-line-2 font-mono text-sm"
                  autoFocus
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Operating Parameters (Description)
                </label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Defines the agent's primary directive and context..."
                  className="bg-elevated border-line-2 resize-none text-sm"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Model
                </label>
                <Input
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="e.g. qwen2.5-coder"
                  className="bg-elevated border-line-2 font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Provider
                </label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full h-10 px-3 text-sm bg-background border border-line-2 rounded-md text-foreground"
                >
                  <option value="">Auto (default provider)</option>
                  {providers.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} ({p.type})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Dossiers autorisés
                </label>
                <div className="min-h-[40px] max-h-[180px] overflow-y-auto p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {folderTree.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">Aucun dossier créé.</span>
                  ) : (
                    folderTree.map((node) => (
                      <FolderTreeNode
                        key={node.id}
                        node={node}
                        depth={0}
                        selected={folderIds}
                        onSelect={setFolderIds}
                      />
                    ))
                  )}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Sélectionner un dossier inclut les ressources qu&apos;il contient (résolues par le Core au runtime — jamais dupliquées). Aucun dossier n&apos;est imposé.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Skills
                </label>
                <div className="flex flex-wrap gap-2 min-h-[40px] p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {skills.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No skills available.</span>
                  ) : (
                    skills.map((skill) => (
                      <label
                        key={skill.id}
                        className={`flex items-center gap-1.5 cursor-pointer ${
                          skill.is_active ? "" : "opacity-45 hover:opacity-70"
                        }`}
                        title={
                          skill.is_active
                            ? `${skill.description || skill.kind}`
                            : "Skill désactivée — elle ne sera pas injectée tant qu'elle est inactive."
                        }
                      >
                        <input
                          type="checkbox"
                          checked={skillIds.includes(skill.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSkillIds((prev) => [...prev, skill.id]);
                            } else {
                              setSkillIds((prev) => prev.filter((id) => id !== skill.id));
                            }
                          }}
                          className="accent-accent"
                        />
                        <span className="text-xs text-foreground-secondary">{skill.name}</span>
                        {skill.kind === "pipeline" ? (
                          <Badge variant="accent" size="sm">Pipeline</Badge>
                        ) : (
                          <Badge variant="info" size="sm">Prompt</Badge>
                        )}
                      </label>
                    ))
                  )}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Les instructions de chaque skill sont injectées dans chaque conversation utilisant cet agent.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Knowledge spécifique
                </label>
                <div className="flex flex-wrap gap-2 min-h-[40px] max-h-[140px] overflow-y-auto p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {knowledgeNodes.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No knowledge nodes available.</span>
                  ) : (
                    knowledgeNodes.map((node) => (
                      <label key={node.id} className="flex items-center gap-1.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={knowledgeNodeIds.includes(node.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setKnowledgeNodeIds((prev) => [...prev, node.id]);
                            } else {
                              setKnowledgeNodeIds((prev) => prev.filter((id) => id !== node.id));
                            }
                          }}
                          className="accent-accent"
                        />
                        <span className="text-xs text-foreground-secondary">{node.label}</span>
                      </label>
                    ))
                  )}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Contenu injecté comme données (sanitisées) dans chaque exécution de cet agent.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  RAG Collections
                </label>
                <div className="min-h-[40px] max-h-[220px] overflow-y-auto p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {collectionTree.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No knowledge available.</span>
                  ) : (
                    collectionTree.map((node) => (
                      <KnowledgeTreeNode
                        key={node.id}
                        node={node}
                        depth={0}
                        selected={collectionIds}
                        onSelect={setCollectionIds}
                      />
                    ))
                  )}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Collections RAG consultées lors des exécutions de cet agent (arborescence définie dans la page Knowledge).
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Tools
                </label>
                <div className="flex flex-wrap gap-2 min-h-[40px] p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {coreToolList.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No tools available.</span>
                  ) : (
                    coreToolList.map((tool) => (
                      <label key={tool.id} className="flex items-center gap-1.5 cursor-pointer" title={tool.description}>
                        <input
                          type="checkbox"
                          checked={toolIds.includes(tool.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setToolIds((prev) => [...prev, tool.id]);
                            } else {
                              setToolIds((prev) => prev.filter((id) => id !== tool.id));
                            }
                          }}
                          className="accent-accent"
                        />
                        <span className="text-xs text-foreground-secondary">{tool.name}</span>
                        <Badge variant="dim" className="text-[9px] px-1 py-0">
                          {tool.provider || "builtin"}
                        </Badge>
                      </label>
                    ))
                  )}
                </div>
                {mcpGroups.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider">
                      MCP
                    </label>
                    {mcpGroups.map(([server, serverTools]) => (
                      <div key={server} className="p-2 bg-elevated/30 border border-line-2 rounded-md">
                        <p className="text-[11px] font-medium text-foreground-secondary mb-1">
                          Serveur : {server}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {serverTools.map((tool) => (
                            <label key={tool.id} className="flex items-center gap-1.5 cursor-pointer" title={tool.description}>
                              <input
                                type="checkbox"
                                checked={toolIds.includes(tool.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setToolIds((prev) => [...prev, tool.id]);
                                  } else {
                                    setToolIds((prev) => prev.filter((id) => id !== tool.id));
                                  }
                                }}
                                className="accent-accent"
                              />
                              <span className="text-xs text-foreground-secondary">{tool.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Outils que le runtime peut invoquer — seuls les outils cochés sont exposés à cet agent (builtin, custom ou MCP). Exécutés par ETHAN Core.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Neural Capabilities
                </label>
                <div className="flex gap-2 mb-3">
                  <Input
                    value={capabilityInput}
                    onChange={(e) => setCapabilityInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddCapability();
                      }
                    }}
                    placeholder="e.g. text-processing"
                    className="bg-elevated border-line-2 h-9 text-sm font-mono"
                  />
                  <Button 
                    type="button" 
                    variant="secondary" 
                    className="h-9 px-3 shrink-0"
                    onClick={handleAddCapability}
                  >
                    <Plus size={16} />
                  </Button>
                </div>
                
                <div className="flex flex-wrap gap-2 min-h-[40px] p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {capabilities.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No capabilities installed.</span>
                  ) : (
                    capabilities.map(cap => (
                      <Badge key={cap} variant="info" className="gap-1 bg-accent/10 text-accent hover:bg-accent/20 transition-colors border-accent/20">
                        {cap}
                        <button
                          type="button"
                          onClick={() => handleRemoveCapability(cap)}
                          className="hover:text-foreground transition-colors ml-1"
                        >
                          <X size={12} />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Aperçu des ressources effectivement autorisées — même arbre
                que GET /v1/agents/{id}/resources (résolu par le Core). */}
            <div className="rounded-lg border border-line-2 bg-elevated/30 p-3">
              <p className="text-xs font-semibold text-foreground-secondary uppercase tracking-wider mb-2">
                Ressources autorisées (aperçu)
              </p>
              <ul className="text-xs text-foreground-secondary space-y-1">
                <li>
                  📁 Dossiers sélectionnés :{" "}
                  {selectedFolders.length === 0
                    ? "aucun"
                    : selectedFolders.map((f) => `${f.name} (${f.resource_count})`).join(", ")}
                </li>
                <li>
                  🧠 Knowledge :{" "}
                  {knowledgeNodes.filter((n) => knowledgeNodeIds.includes(n.id)).map((n) => n.label).join(", ") || "aucun"}
                </li>
                <li>
                  📚 RAG Collections :{" "}
                  {(() => {
                    const names = (ids: string[]) =>
                      flatCollections(collectionTree)
                        .filter((c) => ids.includes(c.id))
                        .map((c) => c.name);
                    return names(collectionIds).join(", ") || "aucune";
                  })()}
                </li>
                <li>
                  🛠️ Skills :{" "}
                  {skills.filter((s) => skillIds.includes(s.id)).map((s) => s.name).join(", ") || "aucun"}
                </li>
                <li>
                  🔧 Tools :{" "}
                  {coreToolList.filter((t) => toolIds.includes(t.id)).map((t) => t.name).join(", ") || "aucun"}
                </li>
                <li>
                  🌐 MCP :{" "}
                  {mcpToolList.filter((t) => toolIds.includes(t.id)).map((t) => t.name).join(", ") || "aucun"}
                </li>
              </ul>
              <p className="mt-2 text-[11px] text-muted-foreground">
                Aucune ressource globale n&apos;est injectée sans sélection explicite.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-line-1 mt-6">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Abort
              </Button>
              <Button type="submit" variant="primary" disabled={isLoading || !name.trim()}>
                {isLoading ? "Processing..." : isEditing ? "Save Parameters" : "Deploy Agent"}
              </Button>
            </div>
          </>
        )}
      </form>
    </Dialog>
  );
}

/** Aplatissement de l'arborescence de collections (toutes profondeurs). */
function flatCollections(nodes: KnowledgeCollectionTree[]): KnowledgeCollectionTree[] {
  return nodes.flatMap((n) => [n, ...flatCollections(n.children)]);
}

/** Nœud récursif de l'arborescence de dossiers — cocher un dossier inclut ses sous-dossiers. */
function FolderTreeNode({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: FolderTree;
  depth: number;
  selected: string[];
  onSelect: React.Dispatch<React.SetStateAction<string[]>>;
}) {
  const descendants = (n: FolderTree): string[] => [
    n.id,
    ...n.children.flatMap(descendants),
  ];

  const allSelected = descendants(node).every((id) => selected.includes(id));
  const someSelected = selected.includes(node.id);

  const handleToggle = (checked: boolean) => {
    const ids = descendants(node);
    onSelect((prev) =>
      checked
        ? [...new Set([...prev, ...ids])]
        : prev.filter((id) => !ids.includes(id)),
    );
  };

  return (
    <div>
      <label
        className="flex items-center gap-1.5 cursor-pointer py-0.5 rounded hover:bg-elevated/60 px-1"
        style={{ paddingLeft: `${depth * 14 + 4}px` }}
      >
        <input
          type="checkbox"
          checked={allSelected}
          ref={(el) => {
            if (el) el.indeterminate = !allSelected && someSelected;
          }}
          onChange={(e) => handleToggle(e.target.checked)}
          className="accent-accent"
        />
        <span className="text-xs text-foreground-secondary">
          📁 {node.name}
        </span>
        <span className="text-[10px] text-muted-foreground">({node.resource_count})</span>
      </label>
      {node.children.map((child) => (
        <FolderTreeNode
          key={child.id}
          node={child}
          depth={depth + 1}
          selected={selected}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

/** Nœud récursif de l'arborescence de collections — cocher un dossier inclut ses sous-dossiers. */
function KnowledgeTreeNode({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: KnowledgeCollectionTree;
  depth: number;
  selected: string[];
  onSelect: React.Dispatch<React.SetStateAction<string[]>>;
}) {
  const descendants = (n: KnowledgeCollectionTree): string[] => [
    n.id,
    ...n.children.flatMap(descendants),
  ];

  const allSelected = descendants(node).every((id) => selected.includes(id));
  const someSelected = selected.includes(node.id);

  const handleToggle = (checked: boolean) => {
    const ids = descendants(node);
    onSelect((prev) =>
      checked
        ? [...new Set([...prev, ...ids])]
        : prev.filter((id) => !ids.includes(id)),
    );
  };

  return (
    <div>
      <label
        className="flex items-center gap-1.5 cursor-pointer py-0.5 rounded hover:bg-elevated/60 px-1"
        style={{ paddingLeft: `${depth * 14 + 4}px` }}
      >
        <input
          type="checkbox"
          checked={allSelected}
          ref={(el) => {
            if (el) el.indeterminate = !allSelected && someSelected;
          }}
          onChange={(e) => handleToggle(e.target.checked)}
          className="accent-accent"
        />
        <span className="text-xs text-foreground-secondary">
          {node.children.length > 0 ? "📁" : "📄"} {node.name}
        </span>
      </label>
      {node.children.map((child) => (
        <KnowledgeTreeNode
          key={child.id}
          node={child}
          depth={depth + 1}
          selected={selected}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
