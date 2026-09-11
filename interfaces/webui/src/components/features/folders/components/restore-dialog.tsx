/**
 * ETHAN WebUI — Restore Dialog
 *
 * Affiche les éléments supprimés (soft-delete) et permet de restaurer
 * ou de vider la corbeille. La logique de restauration vitale réside
 * dans le Core (core/folders) ; ce composant n'envoie que les intents.
 */

"use client";

import {
	Dialog,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
	RotateCcw,
	Trash2,
	AlertTriangle,
	CheckCircle2,
	Archive,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	type ArchiveRequest,
	type DeletedItem,
	listDeletedItems,
	emptyTrash,
	restoreDeletedItem,
	createArchive,
} from "@/lib/api/folders";

interface RestoreDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
}

export function RestoreDialog({ open, onOpenChange }: RestoreDialogProps) {
	const queryClient = useQueryClient();

	const {
		data: deletedItems,
		isLoading,
		isError,
	} = useQuery({
		queryKey: ["deleted-items"],
		queryFn: listDeletedItems,
		enabled: open,
	});

	const restoreMutation = useMutation({
		mutationFn: restoreDeletedItem,
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["deleted-items"] });
		},
	});

	const emptyMutation = useMutation({
		mutationFn: emptyTrash,
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["deleted-items"] });
		},
	});

	const archiveMutation = useMutation({
		mutationFn: (req: ArchiveRequest) => createArchive(req),
		onSuccess: () => {
			onOpenChange(false);
		},
	});

	const handleRestore = async (itemId: string) => {
		await restoreMutation.mutateAsync(itemId);
	};

	const handleEmptyTrash = async () => {
		if (!confirm("Voulez-vous vraiment vider définitivement la corbeille ?")) return;
		await emptyMutation.mutateAsync();
	};

	const handleArchiveDeleted = async () => {
		const folderIds = deletedItems?.filter((i: DeletedItem) => i.type === "folder").map((i: DeletedItem) => i.id) ?? [];
		if (folderIds.length === 0) {
			alert("Aucun dossier à archiver.");
			return;
		}
		const name = prompt("Nom de l\'archive :", `trash_archive_${new Date().toISOString().slice(0, 10)}`);
		if (!name) return;
		await archiveMutation.mutateAsync({
			name,
			folder_ids: folderIds,
			format: "zip",
			compression_level: 6,
			include_metadata: true,
		});
	};

	return (
		<Dialog open={open} onOpenChange={onOpenChange} size="lg" title="Corbeille">
			{isLoading ? (
				<div className="flex items-center justify-center py-8">
					<Spinner className="h-8 w-8" />
					<span className="ml-2">Chargement de la corbeille…</span>
				</div>
			) : isError ? (
				<div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
					<AlertTriangle className="h-4 w-4" />
					Erreur lors du chargement de la corbeille.
				</div>
			) : deletedItems?.length === 0 ? (
				<div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
					<CheckCircle2 className="h-12 w-12 mb-3 opacity-50" />
					<p>La corbeille est vide.</p>
				</div>
			) : (
				<div className="divide-y divide-line-1">
					{deletedItems?.map((item: DeletedItem) => (
						<div key={item.id} className="flex items-center justify-between py-3">
							<div className="min-w-0">
								<div className="font-medium truncate">{item.name}</div>
								<div className="text-xs text-foreground-secondary mt-0.5">
									<span>{item.type}</span>
									<span className="mx-1">·</span>
									<span>{new Date(item.deleted_at).toLocaleString("fr-FR")}</span>
								</div>
							</div>
							<Button
								variant="ghost"
								size="sm"
								onClick={() => handleRestore(item.id)}
								disabled={restoreMutation.isPending}
							>
								<RotateCcw className="h-4 w-4 mr-1" />
								Restaurer
							</Button>
						</div>
					))}
				</div>
			)}

			<div className="flex justify-between pt-4 mt-2 border-t border-line-1">
				<Button
					variant="outline"
					onClick={handleArchiveDeleted}
					disabled={archiveMutation.isPending || !deletedItems?.length}
				>
					{archiveMutation.isPending ? (
						<>
							<Spinner className="h-4 w-4 mr-2" />
							Archivage…
						</>
					) : (
						<>
							<Archive className="h-4 w-4 mr-2" />
							Archiver la corbeille
						</>
					)}
				</Button>
				<Button
					variant="destructive"
					onClick={handleEmptyTrash}
					disabled={emptyMutation.isPending || !deletedItems?.length}
				>
					{emptyMutation.isPending ? (
						<>
							<Spinner className="h-4 w-4 mr-2" />
							Vidage…
						</>
					) : (
						<>
							<Trash2 className="h-4 w-4 mr-2" />
							Vider la corbeille
						</>
					)}
				</Button>
			</div>
		</Dialog>
	);
}
