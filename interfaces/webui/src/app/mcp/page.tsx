// interfaces/webui/src/app/mcp/page.tsx
import { McpServersWorkspace } from '@/components/features/mcp/components/mcp-servers-workspace';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'ETHAN — MCP Servers',
  description: 'Gérer les serveurs MCP connectés à ETHAN.',
};

export default function McpPage() {
  return (
    <main className="container mx-auto p-6">
      <McpServersWorkspace />
    </main>
  );
}