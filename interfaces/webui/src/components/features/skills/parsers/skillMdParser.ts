/** SKILL.md Parser — Parse ECC-compatible Skill manifest files.
 * 
 * Supported format (YAML frontmatter + Markdown content):
 * ---
 * name: <skill-name>
 * description: <skill-description>
 * version: <optional>
 * author: <optional>
 * metadata: <optional, e.g. { openclaw: { os: [...] } }>
 * ...
 * -->
 * ## Instructions
 * <markdown content>
 * 
 * Only supported fields are converted to the ETHAN unified model.
 * Unknown fields are logged but do not cause import failure.
 */

export interface SkillMdImportResult {
  success: boolean
  skill?: {
    name: string
    description: string
    version: string
    author: string
    steps: Array<{ name: string; tool_id?: string }>
    tags: string[]
    metadata: Record<string, unknown>
  }
  errors: string[]
  warnings: string[]
}

/** Parse YAML frontmatter from a string.
 *  Returns { frontmatter, rest } or throws if invalid.
 */
function parseFrontmatter(text: string): { frontmatter: any; rest: string } | null {
  const match = text.match(/^---\s*([\s\S]*?)\s*---\s*(.*)$/)
  if (!match) return null
  const fmText = match[1].trim()
  const rest = match[2].trim()
  
  // Simple YAML parser for key: value pairs
  const frontmatter: any = {}
  const lines = fmText.split('\n')
  for (const line of lines) {
    const pair = line.match(/^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.*)$/)
    if (pair) {
      frontmatter[pair[1]] = pair[2].trim()
    }
  }
  
  return { frontmatter, rest }
}

/** Convert ECC SKILL.md fields to ETHAN unified model. */
function convertToEthanModel(fm: any): { skill: any; errors: string[]; warnings: string[] } {
  const errors: string[] = []
  const warnings: string[] = []
  
  // Required fields
  const name = fm.name
  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    errors.push('Name is required and must be a non-empty string')
    return { skill: null, errors, warnings }
  }
  
  // Description (optional, default empty)
  const description = fm.description || ''
  
  // Version (optional, default "1.0.0")
  const version = fm.version || '1.0.0'
  
  // Author (optional, default "user")
  const author = fm.author || 'user'
  
  // Tags (optional, default empty array)
  const tags: string[] = []
  if (fm.tags) {
    if (Array.isArray(fm.tags)) {
      fm.tags.forEach((t: any) => {
        if (typeof t === 'string' && t.trim().length > 0) {
          tags.push(t.trim())
        }
      })
    } else if (typeof fm.tags === 'string') {
      fm.tags.split(',').forEach((t: string) => {
        if (t.trim().length > 0) {
          tags.push(t.trim())
        }
      })
    }
  }
  
  // Steps (optional, parse from Markdown ## Instructions section)
  const steps: Array<{ name: string; tool_id?: string }> = []
  // We'll parse steps from the Markdown content later
  
  // Metadata (optional, preserve what we can)
  const metadata: Record<string, unknown> = {}
  if (fm.metadata) {
    if (typeof fm.metadata === 'object' && fm.metadata !== null) {
      // Copy relevant fields, exclude known ECC-specific ones
      const allowedKeys = ['openclaw', 'custom'] // fields we want to preserve
      for (const key of Object.keys(fm.metadata)) {
        if (allowedKeys.includes(key)) {
          metadata[key] = fm.metadata[key]
        } else {
          warnings.push(`Unrecognized metadata field: ${key}`)
        }
      }
    }
  }
  
  // Steps would be parsed from the Markdown ## Instructions section
  // For now, empty steps array
  
  return {
    skill: {
      name: name.trim(),
      description: description.trim(),
      version,
      author,
      steps,
      tags,
      metadata,
    },
    errors,
    warnings,
  }
}

/** Main entry point: parse a SKILL.md file and return import result. */
export function parseSkillMd(fileContent: string): SkillMdImportResult {
  const result: SkillMdImportResult = {
    success: false,
    errors: [],
    warnings: [],
  }
  
  // Parse frontmatter
  const parsed = parseFrontmatter(fileContent)
  if (!parsed) {
    result.errors.push('Invalid SKILL.md format: missing YAML frontmatter (--- markers)')
    result.warnings.push('No frontmatter detected — file may not be a valid SKILL.md')
    return result
  }
  
  // Convert to ETHAN model
  const converted = convertToEthanModel(parsed.frontmatter)
  
  if (converted.errors.length > 0) {
    result.errors.push(...converted.errors)
    result.warnings.push(...converted.warnings)
    return result
  }
  
  // Build the import skill object
  const skill: any = {
    name: converted.skill.name,
    description: converted.skill.description,
    version: converted.skill.version,
    author: converted.skill.author,
    tags: converted.skill.tags,
    kind: 'prompt' as const, // Default to prompt; could be detected from content
    content: '', // Will be filled from Markdown content if needed
    metadata: converted.skill.metadata,
  }
  
  result.skill = skill
  result.success = true
  result.warnings.push(...converted.warnings)
  
  return result
}

export { parseFrontmatter, convertToEthanModel }
