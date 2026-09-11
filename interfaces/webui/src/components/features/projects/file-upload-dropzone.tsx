/**
 * ETHAN WebUI — FileUploadDropzone
 *
 * Zone de glisser-déposer pour l'upload de fichiers dans un projet.
 * Le WebUI envoie le fichier brut à l'API Core (multipart) — il ne parse
 * ni n'embede jamais le contenu.
 */

"use client";

import * as React from "react";
import { useUIStore } from "@/store/ui.store";
import { uploadProjectDocument } from "@/lib/api/projects";
import { Upload, FileText } from "lucide-react";

interface FileUploadDropzoneProps {
	projectId: string;
	onUploaded?: () => void;
}

const MAX_SIZE_MB = 50;

export function FileUploadDropzone({ projectId, onUploaded }: FileUploadDropzoneProps) {
	const addToast = useUIStore((s) => s.addToast);
	const [isDragging, setIsDragging] = React.useState(false);
	const [isUploading, setIsUploading] = React.useState(false);
	const [progress, setProgress] = React.useState(0);
	const inputRef = React.useRef<HTMLInputElement>(null);

	const handleFiles = async (files: FileList | null) => {
		if (!files || files.length === 0) return;
		const file = files[0];
		if (file.size > MAX_SIZE_MB * 1024 * 1024) {
			addToast({ type: "error", message: `Fichier trop volumineux (max ${MAX_SIZE_MB} Mo)` });
			return;
		}
		setIsUploading(true);
		setProgress(0);
		try {
			await uploadProjectDocument(projectId, file, (pct) => setProgress(pct));
			addToast({ type: "success", message: `"${file.name}" uploadé avec succès` });
			onUploaded?.();
		} catch (err: any) {
			addToast({ type: "error", message: err.message || "Échec de l'upload" });
		} finally {
			setIsUploading(false);
			setProgress(0);
		}
	};

	const handleDrop = (e: React.DragEvent) => {
		e.preventDefault();
		setIsDragging(false);
		handleFiles(e.dataTransfer.files);
	};

	const handleDragOver = (e: React.DragEvent) => {
		e.preventDefault();
		setIsDragging(true);
	};

	const handleDragLeave = () => setIsDragging(false);

	return (
		<div
			className={`relative rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
				isDragging ? "border-primary bg-primary/5" : "border-line-1/60 hover:border-primary/40"
			}`}
			onDrop={handleDrop}
			onDragOver={handleDragOver}
			onDragLeave={handleDragLeave}
		>
			<input
				ref={inputRef}
				type="file"
				className="hidden"
				accept=".md,.txt,.pdf,.doc,.docx,.csv,.json,.png,.jpg,.jpeg,.webp"
				onChange={(e) => handleFiles(e.target.files)}
			/>
			<div className="flex flex-col items-center gap-3">
				{isUploading ? (
					<>
						<Upload className="h-8 w-8 animate-pulse text-primary" />
						<div className="w-full max-w-xs">
							<div className="h-2 rounded-full bg-line-1">
								<div
									className="h-2 rounded-full bg-primary transition-all"
									style={{ width: `${progress}%` }}
								/>
							</div>
							<p className="mt-1 text-xs text-muted-foreground">{progress}%</p>
						</div>
					</>
				) : (
					<>
						<FileText className="h-8 w-8 text-muted-foreground" />
						<div>
							<p className="text-sm font-medium">
								Glissez-déposez un fichier ici, ou{" "}
								<button
									type="button"
									className="text-primary underline"
									onClick={() => inputRef.current?.click()}
								>
									parcourez
								</button>
							</p>
							<p className="mt-1 text-xs text-muted-foreground">
								MD, TXT, PDF, DOC, DOCX, CSV, JSON, PNG, JPG, WEBP — max {MAX_SIZE_MB} Mo
							</p>
						</div>
					</>
				)}
			</div>
		</div>
	);
}
