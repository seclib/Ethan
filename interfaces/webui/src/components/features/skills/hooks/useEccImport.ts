import { parseSkillMd } from '@/components/features/skills/parsers/skillMdParser'

/** Import Skills from ECC SKILL.md files.
 * 
 * Accepts either:
 * - A single file: File object from file picker
 * - Multiple files: Array of File objects
 * 
 * The function:
 * 1. Parses each SKILL.md file
 * 2. Validates the parsed data
 * 3. Returns a count of imported skills and a list of errors/warnings
 * 4. Does NOT import automatically — requires user confirmation via preview
 */
export async function importEccSkills(
  files: File[],
  onProgress?: (progress: { completed: number; total: number; status: 'parsing' | 'validating' | 'importing' | 'complete' }) => void
): Promise<{
  imported: number
  skipped: number
  errors: string[]
  warnings: string[]
  skills: any[]
}> {
  let importedCount = 0
  const errors: string[] = []
  const warnings: string[] = []
  const skills: any[] = []
  const total = files.length
  
  for (const file of files) {
    if (onProgress) onProgress({ completed: 0, total, status: 'parsing' })
    
    // Check file type
    if (!file.name.match(/\.md$/i)) {
      errors.push(`File "${file.name}" is not a .md file — only .md files are accepted`)
      continue
    }
    
    // Read file content
    try {
      const raw = await file.text()
      
      // Parse the SKILL.md
      const parsed = parseSkillMd(raw)
      
      if (!parsed.success || !parsed.skill) {
        errors.push(`Failed to parse ${file.name}: ${parsed.errors.join(', ')}`)
        continue
      }
      
      // Validate required fields
      if (!parsed.skill.name || parsed.skill.name.trim().length === 0) {
        errors.push(`${file.name}: Skill missing required 'name' field`)
        continue
      }
      
      // Add to import list
      importedCount++
      skills.push(parsed.skill)
      if (onProgress) onProgress({ completed: 1, total, status: 'validating' })
    } catch (err) {
      errors.push(`${file.name}: ${err instanceof Error ? err.message : 'Failed to read file'}`)
    }
  }
  
  if (onProgress) onProgress({ completed: total, total, status: 'complete' })
  
  return {
    imported: importedCount,
    skipped: total - importedCount,
    errors,
    warnings,
    skills
  }
}
