"use client";

/**
 * ProviderFormDialog — Formulaire d'ajout/édition d'un provider LLM.
 *
 * Ne valide AUCUNE logique métier : envoi JSON direct vers Core API /providers.
 */

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Save, X } from "lucide-react"
import type { Provider } from "@/lib/api/providers";

const PROVIDER_TYPES = [
	{ value: "ollama", label: "Ollama (local)" },
	{ value: "openai", label: "OpenAI / Compatible" },
	{ value: "anthropic", label: "Anthropic" },
	{ value: "gemini", label: "Google Gemini" },
	{ value: "azure", label: "Azure OpenAI" },
	{ value: "openrouter", label: "OpenRouter" },
	{ value: "lmstudio", label: "LM Studio" },
	{ value: "llamacpp", label: "llama.cpp" },
	{ value: "vllm", label: "vLLM" },
	{ value: "generic", label: "OpenAI-Compatible (générique)" },
] as const;

interface Props {
	open: boolean;
	mode: "create" | "edit";
	provider: Provider | null;
	onClose: () => void;
	onSubmit: (data: Record<string, unknown>) => Promise<void>;
}

export function ProviderFormDialog({ open, mode, provider, onClose, onSubmit }: Props) {
	const [name, setName] = React.useState(provider?.name ?? "");
	const [type, setType] = React.useState(provider?.type ?? "openai");
	const [base_url, setBaseUrl] = React.useState(provider?.base_url ?? "");
	const [api_key, setApiKey] = React.useState("");
	const [display_name, setDisplayName] = React.useState(provider?.name ?? "");
	const [default_model, setDefaultModel] = React.useState(provider?.default_model ?? "");

	React.useEffect(() => {
		if (provider) {
			setName(provider.name ?? "");
			setType(provider.type ?? "openai");
			setBaseUrl(provider.base_url ?? "");
			setDisplayName(provider.name ?? "");
			setDefaultModel(provider.default_model ?? "");
		}
	}, [provider]);

	const handleSubmit = async () => {
		const data: Record<string, unknown> = {
			name,
			type,
			display_name: display_name || name,
			base_url,
			api_key,
			default_model,
		};
		await onSubmit(data);
		setName("");
		setBaseUrl("");
		setApiKey("");
		setDisplayName("");
		setDefaultModel("");
		onClose();
	};

	const title = mode === "create" ? "Nouveau provider" : "Modifier le provider";
	const submitLabel = mode === "create" ? "Créer" : "Enregistrer";

	return (
		<Dialog open={open} onClose={onClose} title={title} size="md">
			<div className="flex flex-col gap-4">
				<div>
					<label className="block text-sm font-medium mb-1">Type de provider</label>
					<select
						className="w-full rounded-lg border border-line-2 bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
						value={type}
						onChange={(e) => setType(e.target.value as typeof type)}
					>
						{PROVIDER_TYPES.map((t) => (
							<option key={t.value} value={t.value}>
								{t.label}
							</option>
						))}
					</select>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">Nom</label>
					<Input
						placeholder="ex: Ollama local"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">Nom affiché</label>
					<Input
						placeholder="ex: Ollama (local)"
						value={display_name}
						onChange={(e) => setDisplayName(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">URL de base</label>
					<Input
						placeholder="http://localhost:11434"
						value={base_url}
						onChange={(e) => setBaseUrl(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">Clé API</label>
					<Input
						type="password"
						placeholder="••••••••"
						value={api_key}
						onChange={(e) => setApiKey(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">Modèle par défaut</label>
					<Input
						placeholder="ex: llama3.1"
						value={default_model}
						onChange={(e) => setDefaultModel(e.target.value)}
					/>
				</div>

				<div className="flex justify-end gap-2 pt-4 border-t border-line-1">
					<Button variant="secondary" size="sm" onClick={onClose}>
						<X className="h-4 w-4" /> Annuler
					</Button>
					<Button size="sm" onClick={handleSubmit} disabled={!name.trim() || !type}>
						<Save className="h-4 w-4" /> {submitLabel}
					</Button>
				</div>
			</div>
		</Dialog>
	);
}
