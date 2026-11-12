"use client";

/**
 * ModelsPopover — Affiche la liste des modèles disponibles chez un provider.
 *
 * Déclenche une requête Core API /providers/{id}/models à la demande.
 */

import * as React from "react";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, LoaderCircle, Database } from "lucide-react";
import type { Provider } from "@/lib/api/providers";

interface Props {
	providerId: string;
	onRefetch?: () => void;
}

export function ModelsPopover({ providerId, onRefetch }: Props) {
	const [open, setOpen] = React.useState(false);
	const [models, setModels] = React.useState<any[] | null>(null);
	const [loading, setLoading] = React.useState(false);
	const { fetchModels } = useProviders();

	const loadModels = async () => {
		if (!open && !models) {
			setLoading(true);
			try {
				const data = await fetchModels(providerId);
				setModels(data as any[]);
			} catch (e) {
				setModels([]);
			} finally {
				setLoading(false);
			}
		}
	};

	const handleOpen = (nextOpen: boolean) => {
		setOpen(nextOpen);
		if (nextOpen) loadModels();
	};

	return (
		<Popover open={open} onOpenChange={handleOpen}>
			<PopoverTrigger asChild>
				<Button variant="ghost" size="sm" aria-label="Voir les modèles">
					<ChevronDown className="h-4 w-4" />
				</Button>
			</PopoverTrigger>
			<PopoverContent align="end" className="w-64">
				<div className="flex items-center gap-2 mb-2">
					<Database className="h-4 w-4" />
					<span className="font-medium text-sm">Modèles disponibles</span>
				</div>
				{loading && <LoaderCircle className="h-4 w-4 animate-spin mx-auto" />}
				{!loading && models && (
					<div className="space-y-1 max-h-60 overflow-y-auto">
						{models.length === 0 ? (
							<p className="text-xs text-foreground-tertiary text-center py-2">
								Aucun modèle trouvé
							</p>
						) : (
							models.map((m) => (
								<div key={m.id ?? m.name} className="text-xs">
									<span className="font-mono">{m.name ?? m.id}</span>
									{m.context_length && (
										<Badge variant="dim" size="sm" className="ml-2">
											{m.context_length} ctx
										</Badge>
									)}
								</div>
							))
						)}
					</div>
				)}
			</PopoverContent>
		</Popover>
	);
}
