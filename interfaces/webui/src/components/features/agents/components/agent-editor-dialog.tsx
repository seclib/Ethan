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
import { listCollections, type KnowledgeCollection } from "@/lib/api/knowledge";
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
  const [knowledgeIds, setKnowledgeIds] = React.useState<string[]>([]);
  const [toolIds, setToolIds] = React.useState<string[]>([]);

  const { data: providers = [] } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => listProviders(),
  });
  const { data: skills = [] } = useQuery<Skill[]>({
    queryKey: ["skills"],
    queryFn: () => listSkills(),
  });
  const { data: collections = [] } = useQuery<KnowledgeCollection[]>({
    queryKey: ["knowledge-collections"],
    queryFn: () => listCollections(),
  });
  const { data: tools = [] } = useQuery<CoreTool[]>({
    queryKey: ["tools"],
    queryFn: () => listTools(),
  });

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
      setKnowledgeIds((agent.metadata?.knowledge_ids as string[]) || []);
      setToolIds((agent.metadata?.tool_ids as string[]) || []);
    } else if (!isEditing) {
      // Reset form on new
      setName("");
      setDescription("");
      setCapabilities([]);
      setModel("");
      setProvider("");
      setSkillIds([]);
      setKnowledgeIds([]);
      setToolIds([]);
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
          metadata: { knowledge_ids: knowledgeIds, tool_ids: toolIds },
        });
      } else {
        await createAgent({
          name,
          description,
          capabilities,
          model: model || undefined,
          provider: provider || undefined,
          skill_ids: skillIds,
          metadata: { knowledge_ids: knowledgeIds, tool_ids: toolIds },
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
                  Skills
                </label>
                <div className="flex flex-wrap gap-2 min-h-[40px] p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {skills.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No skills available.</span>
                  ) : (
                    skills.map((skill) => (
                      <label key={skill.id} className="flex items-center gap-1.5 cursor-pointer">
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
                  Knowledge
                </label>
                <div className="flex flex-wrap gap-2 min-h-[40px] p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {collections.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No knowledge available.</span>
                  ) : (
                    collections.map((collection) => (
                      <label key={collection.id} className="flex items-center gap-1.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={knowledgeIds.includes(collection.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setKnowledgeIds((prev) => [...prev, collection.id]);
                            } else {
                              setKnowledgeIds((prev) => prev.filter((id) => id !== collection.id));
                            }
                          }}
                          className="accent-accent"
                        />
                        <span className="text-xs text-foreground-secondary">{collection.name}</span>
                      </label>
                    ))
                  )}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Documents RAG automatiquement consultés dans chaque conversation utilisant cet agent.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                  Tools
                </label>
                <div className="flex flex-wrap gap-2 min-h-[40px] p-2 bg-elevated/50 border border-line-2 rounded-md">
                  {tools.length === 0 ? (
                    <span className="text-xs text-muted-foreground p-1 italic">No tools available.</span>
                  ) : (
                    tools.map((tool) => (
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
                        <Badge variant={tool.provider === "builtin" ? "dim" : "info"} className="text-[9px] px-1 py-0">
                          {tool.provider}
                        </Badge>
                      </label>
                    ))
                  )}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Outils que le LLM peut invoquer (builtin, custom ou MCP découverts). Exécutés par ETHAN Core.
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
