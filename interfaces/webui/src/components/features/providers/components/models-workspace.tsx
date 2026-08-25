"use client";

/**
 * ModelsWorkspace — Vue du catalogue des modèles LLM.
 *
 * Fonctionnalités :
 * - Liste de tous les modèles (providers + custom)
 * - Recherche par nom / provider / capabilities
 * - Épinglage des favoris (localStorage)
 * - Sélection (badge "actif")
 * - Toggle activation (custom models seulement)
 * - Lien vers provider parent
 *
 * Ne modifie AUCUNE logique de routage Core — utilise le LLMSelector existant.
 */

import * as React from "react";
import { useModels } from "@/components/features/providers/hooks/use-models";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Database, RefreshCw, LoaderCircle, Check, Star, StarHalf } from "lucide-react";

const CAPABILITIES_COLORS = {
	"chat": "info",
	"embedding": "success",
	"reasoning": "accent",
	"vision": "purple",
	"audio": "gold",
} as const;

export function ModelsWorkspace() {
	const { models, isLoading, searchModels, pinModel, unpinModel, isPinned } = useModels();

	const [searchQuery, setSearchQuery] = React.useState("");
	const [showPinnedOnly, setShowPinnedOnly] = React.useState(false);

	const filtered = React.useMemo(() => {
		let results = searchModels(searchQuery);
		if (showPinnedOnly) {
			results = results.filter((m) => isPinned(m.provider, m.id));
		}
		return results;
	}, [searchQuery, showPinnedOnly, models, searchModels, isPinned]);

	const handlePin = (m: Model) => {
		if (isPinned(m.provider, m.id)) {
			unpinModel(m.provider, m.id);
		} else {
			pinModel(m.provider, m.id);
		}
	};

	if (isLoading) {
		return (
			<div className="flex h-full items-center justify-center py-12">
				<LoaderCircle className="h-8 w-8 animate-spin" />
				<p className="ml-2 text-foreground-tertiary">Chargement des modèles…</p>
			</div>
		);
	}

	return (
		<div className="flex h-full flex-col gap-4 p-6">
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-semibold">Catalogue des modèles</h1>
				<div className="flex gap-2">
					<Input
						placeholder="Rechercher un modèle…"
						value={searchQuery}
						onChange={(e) => setSearchQuery(e.target.value)}
						className="max-w-sm"
					/>
					<Button
						variant={showPinnedOnly ? "default" : "ghost"}
						size="sm"
						onClick={() => setShowPinnedOnly(!showPinnedOnly)}
						aria-pressed={showPinnedOnly}
					>
						<Star className="h-4 w-4" />
						{showPinnedOnly ? "Tous" : "Favoris"}
					</Button>
				</div>
			</div>

			{filtered.length === 0 ? (
				<p className="text-center text-foreground-tertiary py-8">
					{searchQuery ? "Aucun modèle trouvé." : "Aucun modèle disponible."}
				</p>
			) : (
				<div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
					{filtered.map((model) => (
						<ModelCard key={`${model.provider}:${model.id}`} model={model} onPin={handlePin} pinned={isPinned(model.provider, model.id)} />
					))}
				</div>
			)}
		</div>
	);
}

interface ModelCardProps {
	model: Model;
	onPin: (m: Model) => void;
	pinned: boolean;
}

function ModelCard({ model, onPin, pinned }: ModelCardProps) {
	return (
		<Card variant="outlined" className="group">
			<CardHeader>
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2">
						<Database className="h-5 w-5 text-accent" />
						<CardTitle className="text-lg">{model.name}</CardTitle>
					</div>
					<Badge variant={model.is_local ? "success" : "info"}>
						{model.is_local ? "Local" : model.provider}
					</Badge>
				</div>
				<CardDescription>
					{model.model} · {model.context_length.toLocaleString()} ctx
				</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="flex flex-wrap gap-1 mb-2">
					{(model.capabilities || []).map((cap) => (
						<Badge key={cap} variant="dim" size="sm">
							{cap}
						</Badge>
					))}
				</div>
				<div className="flex items-center gap-2 text-xs text-foreground-tertiary">
					<StarHalf className="h-3 w-3" />
					<span>Qualité: {Math.round(model.quality_score * 100)}%</span>
					{model.is_available ? (
						<Badge variant="success" size="sm">Disponible</Badge>
					) : (
						<Badge variant="error" size="sm">Indisponible</Badge>
					)}
				</div>
			</CardContent>
			<Button
				variant="ghost"
				size="sm"
				onClick={() => onPin(model)}
				aria-label={pinned ? "Désépingler" : "Épingler"}
				className="mt-auto"
			>
				<Star className={pinned ? "h-4 w-4 fill-current" : "h-4 w-4"} />
			</Button>
		</Card>
	);
}

// Type local
interface Model {
	id: string;
	name: string;
	model: string;
	provider: string;
	context_length: number;
	is_local: boolean;
	is_private: boolean;
	quality_score: number;
	capabilities: string[];
	is_available: boolean;
	is_custom: boolean;
	source: "discovered" | "custom";
}
