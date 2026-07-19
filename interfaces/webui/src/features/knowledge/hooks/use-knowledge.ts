"use client";

import { useQuery } from "@tanstack/react-query";
import { knowledgeService } from "@/features/knowledge/services/knowledge.service";
import { useState } from "react";

export interface KnowledgeNode {
  id: string;
  label: string;
  type: string;
  connections: string[];
}

export function useKnowledge() {
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);
  
  const { data: nodes = [], isLoading, error, refetch } = useQuery<KnowledgeNode[]>({
    queryKey: ["knowledgeNodes"],
    queryFn: () => knowledgeService.getAll() as Promise<KnowledgeNode[]>,
  });

  return {
    nodes,
    selectedNode,
    isLoading,
    error: error instanceof Error ? error.message : null,
    fetchNodes: refetch,
    searchNodes: async (query: string) => {
      // Typically we'd use useMutation or another query, but to keep the interface simple:
      const results = await knowledgeService.search(query) as KnowledgeNode[];
      return results;
    },
    selectNode: setSelectedNode,
  };
}
