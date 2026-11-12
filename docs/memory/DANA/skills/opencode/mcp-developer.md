# MCP Developer (mcp-developer)

**Source :** `/home/fatsio/.config/opencode/skills/mcp-developer/SKILL.md`  \n**Domaine :** Protocol — MCP  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

MCP (Model Context Protocol) server/client development. Tool handlers, resource providers, stdio/HTTP/SSE transport layers, Zod/Pydantic schema validation, protocol compliance debugging, SDK construction (TypeScript/Python).

## Main capabilities

- **Tool handlers**: Creates tool execution handlers for MCP protocol messages
- **Resource providers**: Implements resource serving for MCP protocol
- **Transport layers**: Configures stdio, HTTP, and SSE transport for MCP communication
- **Schema validation**: Uses Zod (TypeScript) or Pydantic (Python) for message validation
- **Protocol debugging**: Debug MCP protocol compliance and message formatting
- **SDK construction**: Builds TypeScript or Python SDKs for MCP integration

## What it can do

- Define MCP tool handlers with proper input/output schemas
- Set up MCP resource providers with content negotiation
- Configure stdio transport for local process communication
- Set up HTTP/SSE transport for remote MCP server communication
- Validate MCP messages using Zod or Pydantic schemas
- Build client SDKs for consuming MCP services

## When it is useful

- Integrating AI systems with MCP protocol
- Building tool-enabled AI assistants with standardized tool access
- Creating MCP server implementations for code analysis
- Setting up cross-agent communication via MCP
- Developing plugin architectures with standardized interfaces

## Practical examples

### MCP tool handler

```typescript
// Tool handler for file reading
const readFileTool: ToolHandler = {
  name: "read_file",
  description: "Read a file from the filesystem",
  schema: z.object({
    path: z.string().describe("File path to read"),
  }),
  handler: async ({ path }) => {
    const content = await Deno.readTextFile(path);
    return { content };
  },
};
```

### MCP message validation with Zod

```typescript
const mcpMessageSchema = z.object({
  jsonrpc: z.literal("2.0"),
  id: z union([z.string(), z.number(), z.null()]),
  method: z.string(),
  params: z.object({}),
});

type MCPMessage = z.infer<typeof mcpMessageSchema>;
```

### Python MCP resource provider

```python
from mcp.server import Server
from mcp.types import Resource

server = Server("my-mcp-server")

@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="text://file.md",
            name="My Markdown File",
            description="A markdown file resource",
        )
    ]
```

## Original source path

`/home/fatsio/.config/opencode/skills/mcp-developer/SKILL.md`

## Classification

- **Domaines :** protocol, MCP, outil, SDK, intégration
- **Statut :** Spécialisé (Niveau B)
- **Références :** `api-design`, `mcp-server-patterns`, `agent-security-hardening`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis
