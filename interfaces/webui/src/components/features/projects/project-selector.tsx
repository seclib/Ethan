/**
 * ETHAN WebUI — ProjectSelector
 *
 * Lightweight project switcher for the Chat header.
 * Uses the unified Projects store (core/projects source of truth)
 * via /v1/projects* endpoints.
 *
 * Uses project-native UI primitives (custom Dialog, Button, Input) —
 * no shadcn-ui imports here.
 */

'use client';

import * as React from 'react';
import { useProjectsStore } from '@/lib/store/projects';
import { Project } from '@/lib/api/projects';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';
import { useUIStore } from '@/store/ui.store';
import { Plus, CheckSquare, Square, ChevronDown } from 'lucide-react';

const GENERAL_PROJECT: Project = {
	id: 'general',
	name: 'General (Default)',
	description: 'Conversation scope without Knowledge or specific context.',
	user_id: 'current',
	folder_ids: [],
	knowledge_ids: [],
	collection_ids: [],
	skill_ids: [],
	tool_ids: [],
	created_at: '',
	updated_at: '',
	metadata: {},
};

export function ProjectSelector() {
	const {
		projects,
		activeProject,
		loadProjects,
		createProject,
		setActiveProject,
	} = useProjectsStore();
	const addToast = useUIStore((s) => s.addToast);
	const [showCreateDialog, setShowCreateDialog] = React.useState(false);
	const [newProjectName, setNewProjectName] = React.useState('');
	const [isSubmitting, setIsSubmitting] = React.useState(false);

	const allProjects = React.useMemo(() => [GENERAL_PROJECT, ...projects], [projects]);
	const currentId = activeProject?.id ?? 'general';
	const currentName = allProjects.find((p) => p.id === currentId)?.name ?? 'Select project';

	const handleCreate = async () => {
		if (!newProjectName.trim() || isSubmitting) return;
		setIsSubmitting(true);
		try {
			await createProject({ name: newProjectName.trim() });
			await loadProjects();
			setShowCreateDialog(false);
			setNewProjectName('');
			addToast({ type: 'success', message: `Project "${newProjectName.trim()}" created` });
		} catch (err: any) {
			addToast({ type: 'error', message: err.message || 'Failed to create project' });
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleSwitch = async (val: string) => {
		try {
			if (val === 'general') {
				await setActiveProject(null);
				addToast({ type: 'success', message: 'Switched to General' });
			} else {
				await setActiveProject(val);
				const found = allProjects.find((p) => p.id === val);
				addToast({ type: 'success', message: `Switched to "${found?.name ?? 'project'}"` });
			}
		} catch (err: any) {
			addToast({ type: 'error', message: err.message || 'Failed to switch project' });
		}
	};

	// Dropdown custom pour le sélecteur de projet
	const [dropdownOpen, setDropdownOpen] = React.useState(false);

	return (
		<div className="relative inline-flex items-center gap-2">
			{/* Sélecteur de projet */}
			<button
				type="button"
				onClick={() => setDropdownOpen(!dropdownOpen)}
				className="flex items-center gap-2 rounded-md border border-line-1/60 bg-background px-3 py-1.5 text-sm font-medium hover:bg-accent focus:outline-none focus:ring-2 focus:ring-accent"
				aria-haspopup="listbox"
				aria-expanded={dropdownOpen}
			>
				<span className="max-w-[180px] truncate">
					{currentName}
				</span>
				<ChevronDown className="h-4 w-4 opacity-60" />
			</button>

			{dropdownOpen && (
				<div
					className="absolute top-full left-0 z-popover mb-1 w-64 max-h-80 overflow-y-auto rounded-md border border-line-1/60 bg-background shadow-lg"
					onKeyDown={(e) => e.stopPropagation()}
				>
					<ul className="py-1 text-sm" role="listbox">
						{allProjects.map((proj) => (
							<li key={proj.id}>
								<button
									type="button"
									className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-accent"
									onClick={() => {
										setDropdownOpen(false);
										void handleSwitch(proj.id);
									}}
								>
									{currentId === proj.id ? (
										<CheckSquare className="h-4 w-4 text-accent" />
									) : (
										<Square className="h-4 w-4 opacity-40" />
									)}
									<span className="truncate">{proj.name}</span>
								</button>
							</li>
						))}
					</ul>
				</div>
			)}

			{/* Click-outside pour fermer le dropdown */}
			{dropdownOpen && (
				<div
					className="fixed inset-0 z-0"
					onClick={() => setDropdownOpen(false)}
					aria-hidden="true"
				/>
			)}

			{/* Créer un nouveau projet */}
			<Button
				variant="ghost"
				size="sm"
				onClick={() => setShowCreateDialog(true)}
				aria-label="Create new project"
			>
				<Plus className="h-4 w-4" />
			</Button>

			<Dialog
				open={showCreateDialog}
				title="Create Project"
				onClose={() => setShowCreateDialog(false)}
			>
				<div className="space-y-4 py-2">
					<div className="space-y-2">
						<label className="text-sm font-medium">Project Name</label>
						<Input
							value={newProjectName}
							onChange={(e) => setNewProjectName(e.target.value)}
							placeholder="e.g., OSINT Research"
							disabled={isSubmitting}
						/>
					</div>
					<div className="text-sm text-muted-foreground">
						A project scopes conversations and can attach knowledge,
						skills, tools, and an agent. No resources are added automatically.
					</div>
				</div>
				<div className="flex justify-end gap-2 pt-4 border-t">
					<Button
						variant="outline"
						size="sm"
						onClick={() => setShowCreateDialog(false)}
						disabled={isSubmitting}
					>
						Cancel
					</Button>
					<Button
						size="sm"
						onClick={handleCreate}
						disabled={!newProjectName.trim() || isSubmitting}
					>
						{isSubmitting ? 'Creating...' : 'Create'}
					</Button>
				</div>
			</Dialog>
		</div>
	);
}
