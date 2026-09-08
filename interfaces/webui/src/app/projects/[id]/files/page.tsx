/**
 * ETHAN WebUI — Project Files Page
 *
 * Gestion des fichiers d'un projet : upload (drag & drop), liste, suppression.
 * Le WebUI est un client passif — toute la logique (extraction, chunking,
 * embedding) est déléguée au pipeline Core via l'API.
 */

"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { FileUploadDropzone } from "@/components/features/projects/file-upload-dropzone";
import { ProjectFilesTable } from "@/components/features/projects/project-files-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ProjectFilesPage() {
	const params = useParams();
	const projectId = params.id as string;
	const [refreshKey, setRefreshKey] = React.useState(0);

	const handleUploaded = () => setRefreshKey((k) => k + 1);

	return (
		<div className="mx-auto max-w-4xl space-y-6 p-6">
			<div className="flex items-center gap-3">
				<Link
					href={`/projects/${projectId}`}
					className="rounded p-1 text-muted-foreground hover:bg-accent"
					aria-label="Retour au projet"
				>
					<ArrowLeft className="h-5 w-5" />
				</Link>
				<div>
					<h1 className="text-lg font-semibold">Fichiers du projet</h1>
					<p className="text-sm text-muted-foreground">
						Uploadez des documents (MD, TXT, PDF, DOCX, CSV, JSON, images) pour les indexer dans le RAG du projet.
					</p>
				</div>
			</div>

			<FileUploadDropzone projectId={projectId} onUploaded={handleUploaded} />

			<div>
				<h2 className="mb-3 text-sm font-medium">Documents indexés</h2>
				<ProjectFilesTable
					projectId={projectId}
					refreshKey={refreshKey}
					onDeleted={handleUploaded}
				/>
			</div>
		</div>
	);
}
