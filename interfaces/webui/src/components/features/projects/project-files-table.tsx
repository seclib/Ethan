/**
 * ETHAN WebUI — ProjectFilesTable
 *
 * Tableau des fichiers d'un projet (lecture seule côté WebUI).
 * Les actions (suppression) délèguent à l'API Core.
 */

"use client";

import * as React from "react";
import { useUIStore } from "@/store/ui.store";
import {
	listProjectDocuments,
	deleteProjectDocument,
	type ProjectDocument,
} from "@/lib/api/projects";
import { Trash2, FileText, FileImage, File, Loader2, AlertCircle } from "lucide-react";

interface ProjectFilesTableProps {
	projectId: string;
	refreshKey: number;
	onDeleted?: () => void;
}

function StatusBadge({ status }: { status: ProjectDocument["status"] }) {
	if (status === "processing") return <span className="flex items-center gap-1 text-xs text-amber-500"><Loader2 className="h-3 w-3 animate-spin" />Traitement</span>;
	if (status === "failed") return <span className="flex items-center gap-1 text-xs text-red-500"><AlertCircle className="h-3 w-3" />Échec</span>;
	return <span className="text-xs text-green-600">✓ Indexé</span>;
}

function FileIcon({ mime }: { mime: string }) {
	if (mime.startsWith("image/")) return <FileImage className="h-4 w-4 text-blue-500" />;
	if (mime.includes("pdf") || mime.includes("word") || mime.includes("document")) return <FileText className="h-4 w-4 text-red-500" />;
	return <File className="h-4 w-4 text-muted-foreground" />;
}

export function ProjectFilesTable({ projectId, refreshKey, onDeleted }: ProjectFilesTableProps) {
	const addToast = useUIStore((s) => s.addToast);
	const [docs, setDocs] = React.useState<ProjectDocument[]>([]);
	const [loading, setLoading] = React.useState(true);

	const load = React.useCallback(async () => {
		setLoading(true);
		try {
			const data = await listProjectDocuments(projectId);
			setDocs(data);
		} catch (err: any) {
			addToast({ type: "error", message: err.message || "Échec du chargement" });
		} finally {
			setLoading(false);
		}
	}, [projectId, addToast]);

	React.useEffect(() => {
		load();
	}, [load, refreshKey]);

	const handleDelete = async (doc: ProjectDocument) => {
		if (!confirm(`Supprimer "${doc.filename}" ?`)) return;
		try {
			await deleteProjectDocument(projectId, doc.id);
			addToast({ type: "success", message: `"${doc.filename}" supprimé` });
			onDeleted?.();
		} catch (err: any) {
			addToast({ type: "error", message: err.message || "Échec de la suppression" });
		}
	};

	if (loading) return <div className="flex items-center justify-center p-8 text-sm text-muted-foreground"><Loader2 className="mr-2 h-4 w-4 animate-spin" />Chargement...</div>;
	if (docs.length === 0) return <div className="p-8 text-center text-sm text-muted-foreground">Aucun fichier dans ce projet. Uploadez votre premier document.</div>;

	return (
		<div className="overflow-hidden rounded-md border border-line-1/60">
			<table className="w-full text-sm">
				<thead className="bg-muted">
					<tr className="text-left text-xs text-muted-foreground">
						<th className="px-4 py-2">Fichier</th>
						<th className="px-4 py-2">Type</th>
						<th className="px-4 py-2">Taille</th>
						<th className="px-4 py-2">Statut</th>
						<th className="px-4 py-2"></th>
					</tr>
				</thead>
				<tbody>
					{docs.map((doc) => (
						<tr key={doc.id} className="border-t border-line-1/40 hover:bg-muted">
							<td className="px-4 py-2">
								<div className="flex items-center gap-2">
									<FileIcon mime={doc.mime_type} />
									<span className="max-w-[200px] truncate">{doc.filename}</span>
								</div>
							</td>
							<td className="px-4 py-2 text-xs text-muted-foreground">{doc.mime_type}</td>
							<td className="px-4 py-2 text-xs text-muted-foreground">{formatSize(doc.size_bytes)}</td>
							<td className="px-4 py-2"><StatusBadge status={doc.status} /></td>
							<td className="px-4 py-2 text-right">
								<button
									type="button"
									className="rounded p-1 text-muted-foreground hover:bg-red-500/10 hover:text-red-500"
									onClick={() => handleDelete(doc)}
									aria-label={`Supprimer ${doc.filename}`}
								>
									<Trash2 className="h-4 w-4" />
								</button>
							</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
}

function formatSize(bytes: number): string {
	if (bytes < 1024) return `${bytes} o`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}
