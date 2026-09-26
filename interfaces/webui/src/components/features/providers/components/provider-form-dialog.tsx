"use client";

/**
 * ProviderFormDialog — Formulaire d'ajout/édition d'un provider LLM.
 *
 * Le formulaire est piloté par le CATALOGUE CORE (GET /providers/catalog) :
 * types acceptés par la factory, URL de base par défaut, méthodes
 * d'authentification et capacités déclarées proviennent d'ETHAN Core.
 * Le WebUI ne maintient aucune liste parallèle (règle AGENTS.md).
 *
 * - Aucune validation métier ici : le Core valide et normalise (400 explicite).
 * - La clé API n'est jamais pré-remplie (le Core ne la renvoie jamais) :
 *   ``has_api_key`` n'est qu'un indicateur d'état ; un champ vide = conserver.
 * - Les paramètres techniques (api_version Azure, options JSON) vivent dans
 *   la section « Advanced » repliée : ils n'encombrent pas l'UX principale.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { capabilityLabel, capabilityVariant } from "@/lib/llm/capabilities";
import {
	getProviderCatalog,
	type Provider,
	type ProviderTypeCatalogEntry,
} from "@/lib/api/providers";
import { AlertCircle, ChevronDown, ChevronRight, Lock, Save, X } from "lucide-react";

/**
 * Libellés d'affichage des types connus. La LISTE des types vient du Core ;
 * un type inconnu du WebUI est affiché brut (id Core), jamais renommé.
 */
const PROVIDER_TYPE_LABELS: Record<string, string> = {
	ollama: "Ollama (local)",
	openai: "OpenAI",
	azure: "Azure OpenAI",
	anthropic: "Anthropic",
	vllm: "vLLM (local)",
	llamacpp: "llama.cpp (local)",
	lmstudio: "LM Studio (local)",
	gemini: "Google Gemini",
	"openai-compatible": "OpenAI-Compatible (générique)",
	openrouter: "OpenRouter",
	custom: "Custom (OpenAI-Compatible)",
};

interface Props {
	open: boolean;
	mode: "create" | "edit";
	provider: Provider | null;
	onClose: () => void;
	onSubmit: (data: Record<string, unknown>) => Promise<void>;
}

function typeLabel(entry: ProviderTypeCatalogEntry): string {
	return PROVIDER_TYPE_LABELS[entry.id] ?? entry.id;
}

export function ProviderFormDialog({ open, mode, provider, onClose, onSubmit }: Props) {
	const catalogQuery = useQuery({
		queryKey: ["provider-catalog"],
		queryFn: getProviderCatalog,
		staleTime: 5 * 60_000,
	});

	const [name, setName] = React.useState("");
	const [type, setType] = React.useState("");
	const [baseUrl, setBaseUrl] = React.useState("");
	const [apiKey, setApiKey] = React.useState("");
	const [displayName, setDisplayName] = React.useState("");
	const [defaultModel, setDefaultModel] = React.useState("");
	const [authMethod, setAuthMethod] = React.useState<"api_key" | "user_account">("api_key");
	const [advancedOpen, setAdvancedOpen] = React.useState(false);
	const [apiVersion, setApiVersion] = React.useState("");
	const [optionsText, setOptionsText] = React.useState("");
	const [optionsError, setOptionsError] = React.useState<string | null>(null);
	// L'URL de base n'est auto-remplie que tant que l'utilisateur ne l'a pas
	// modifiée lui-même (sinon on écrase une saisie explicite).
	const [baseUrlTouched, setBaseUrlTouched] = React.useState(false);

	const catalogTypes = catalogQuery.data?.types ?? [];
	const currentType = catalogTypes.find((entry) => entry.id === type) ?? null;

	// Seed depuis le provider édité / le premier type du catalogue en création.
	React.useEffect(() => {
		if (!open) return;
		setOptionsError(null);
		setOptionsText("");
		setApiVersion("");
		setAdvancedOpen(false);
		setAuthMethod("api_key");
		if (provider) {
			setName(provider.name ?? "");
			setType(provider.type ?? "");
			setBaseUrl(provider.base_url ?? "");
			setDisplayName(provider.name ?? "");
			setDefaultModel(provider.default_model ?? "");
			setBaseUrlTouched(Boolean(provider.base_url));
			if (provider.auth_methods?.includes("user_account")) setAuthMethod("user_account");
		} else {
			setName("");
			setBaseUrl("");
			setDisplayName("");
			setDefaultModel("");
			setApiKey("");
			setBaseUrlTouched(false);
			setType(catalogTypes[0]?.id ?? "");
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps -- seed à l'ouverture
	}, [open, provider]);

	// Auto-remplissage de l'URL par défaut (source : Core) quand le type change.
	React.useEffect(() => {
		if (baseUrlTouched) return;
		if (currentType?.default_base_url) setBaseUrl(currentType.default_base_url);
	}, [currentType, baseUrlTouched]);

	// Sélectionne le premier type du catalogue dès qu'il est chargé (création).
	React.useEffect(() => {
		if (mode !== "create" || type || catalogTypes.length === 0) return;
		setType(catalogTypes[0].id);
	}, [mode, type, catalogTypes]);

	const supportsAccount = (currentType?.auth_methods ?? []).includes("user_account");
	const isCreate = mode === "create";
	const catalogError = catalogQuery.isError;

	const parseOptions = (): Record<string, unknown> | null => {
		const trimmed = optionsText.trim();
		let options: Record<string, unknown> = {};
		if (trimmed) {
			try {
				const parsed = JSON.parse(trimmed);
				if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
					setOptionsError("Les options doivent être un objet JSON.");
					return null;
				}
				options = parsed as Record<string, unknown>;
			} catch {
				setOptionsError("JSON invalide.");
				return null;
			}
		}
		if (apiVersion.trim()) options.api_version = apiVersion.trim();
		setOptionsError(null);
		return options;
	};

	const handleSubmit = async () => {
		const options = parseOptions();
		if (options === null) return;

		const data: Record<string, unknown> = {
			display_name: displayName || name,
			base_url: baseUrl,
			default_model: defaultModel,
		};
		if (isCreate) {
			data.name = name.trim();
			data.type = type;
		}
		// Clé API : envoyée UNIQUEMENT si l'utilisateur en saisit une nouvelle.
		if (apiKey.trim()) data.api_key = apiKey.trim();
		// Options : envoyées uniquement si renseignées (le Core ne les renvoie
		// jamais — un champ vide signifie « conserver l'existant »).
		if (Object.keys(options).length > 0) data.options = options;

		await onSubmit(data);
		onClose();
	};

	const canSubmit =
		!catalogError && (isCreate ? name.trim().length > 0 && type.length > 0 : true);

	const title = isCreate ? "Nouveau provider" : "Modifier le provider";
	const submitLabel = isCreate ? "Créer" : "Enregistrer";

	return (
		<Dialog open={open} onClose={onClose} title={title} size="md">
			<div className="flex flex-col gap-4">
				{catalogError && (
					<div className="flex items-start gap-2 rounded-lg border border-red-soft bg-red-soft/50 px-3 py-2 text-sm text-red">
						<AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
						<span>
							Catalogue des providers indisponible (ETHAN Core) — impossible de
							créer ou modifier un provider pour l&apos;instant.
						</span>
					</div>
				)}

				{isCreate && (
					<div>
						<label className="block text-sm font-medium mb-1" htmlFor="provider-name">
							Identifiant (ID Core)
						</label>
						<Input
							id="provider-name"
							placeholder="ex: ollama-local"
							value={name}
							onChange={(e) => setName(e.target.value)}
						/>
						<p className="mt-1 text-xs text-foreground-tertiary">
							Identifiant unique utilisé par ETHAN Core (lettres, chiffres, tirets).
						</p>
					</div>
				)}

				{!isCreate && provider && (
					<div>
						<label className="block text-sm font-medium mb-1">Identifiant (ID Core)</label>
						<Input value={provider.id} readOnly disabled />
						<p className="mt-1 text-xs text-foreground-tertiary">
							L&apos;identifiant n&apos;est pas modifiable.
						</p>
					</div>
				)}

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="provider-display-name">
						Nom affiché
					</label>
					<Input
						id="provider-display-name"
						placeholder="ex: Ollama (local)"
						value={displayName}
						onChange={(e) => setDisplayName(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="provider-type">
						Type de provider
					</label>
					<select
						id="provider-type"
						className="w-full rounded-md border border-line-1 bg-bg-1 px-3 py-2 text-sm text-foreground"
						value={type}
						disabled={!isCreate}
						onChange={(e) => setType(e.target.value)}
					>
						{catalogQuery.isLoading && <option value="">Chargement du catalogue…</option>}
						{catalogTypes.map((entry) => (
							<option key={entry.id} value={entry.id}>
								{typeLabel(entry)}
							</option>
						))}
					</select>
					<p className="mt-1 text-xs text-foreground-tertiary">
						Types supportés par ETHAN Core
						{!isCreate ? " — le type n'est pas modifiable après création." : "."}
					</p>
				</div>

				{currentType && currentType.capabilities.length > 0 && (
					<div className="flex flex-wrap items-center gap-1.5">
						<span className="text-xs text-foreground-tertiary">
							Capacités déclarées par le Core :
						</span>
						{currentType.capabilities.map((capability) => (
							<Badge key={capability} variant={capabilityVariant(capability)} size="sm">
								{capabilityLabel(capability)}
							</Badge>
						))}
					</div>
				)}

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="provider-base-url">
						URL de base
					</label>
					<Input
						id="provider-base-url"
						placeholder={currentType?.default_base_url || "https://api.example.com/v1"}
						value={baseUrl}
						onChange={(e) => {
							setBaseUrl(e.target.value);
							setBaseUrlTouched(true);
						}}
					/>
					<p className="mt-1 text-xs text-foreground-tertiary">
						{currentType?.default_base_url
							? `Valeur par défaut du type (Core) : ${currentType.default_base_url}`
							: "Ce type ne définit pas d'endpoint par défaut — saisissez l'URL officielle."}
					</p>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">Méthode de connexion</label>
					<div className="flex flex-col gap-1.5">
						<label className="flex items-center gap-2 text-sm cursor-pointer">
							<input
								type="radio"
								name="auth_method"
								checked={authMethod === "api_key"}
								onChange={() => setAuthMethod("api_key")}
							/>
							API Key
						</label>
						<label
							className="flex items-center gap-2 text-sm cursor-pointer"
							title={
								supportsAccount
									? "Connexion via votre compte provider (OAuth, géré par ETHAN Core)"
									: "Non supporté : ETHAN Core ne déclare pas de connexion par compte pour ce type"
							}
						>
							<input
								type="radio"
								name="auth_method"
								checked={authMethod === "user_account"}
								disabled={!supportsAccount}
								onChange={() => setAuthMethod("user_account")}
							/>
							<span className={!supportsAccount ? "opacity-50" : ""}>
								User Account / OAuth
							</span>
						</label>
					</div>
					{!supportsAccount && (
						<p className="mt-1 text-xs text-foreground-tertiary">
							La connexion par compte utilisateur (OAuth) n&apos;est pas déclarée par
							ETHAN Core pour ce type — la clé API reste la méthode de référence.
						</p>
					)}
				</div>

				{authMethod === "api_key" && (
					<div>
						<label className="block text-sm font-medium mb-1" htmlFor="provider-api-key">
							Clé API
						</label>
						<Input
							id="provider-api-key"
							type="password"
							placeholder={
								provider?.has_api_key
									? "•••••••• (clé déjà configurée — laisser vide pour conserver)"
									: "••••••••"
							}
							value={apiKey}
							onChange={(e) => setApiKey(e.target.value)}
						/>
						{provider?.has_api_key && (
							<p className="mt-1 flex items-center gap-1 text-xs text-foreground-tertiary">
								<Lock className="h-3 w-3" />
								Clé configurée côté Core — jamais affichée ni renvoyée.
							</p>
						)}
					</div>
				)}

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="provider-default-model">
						Modèle par défaut
					</label>
					<Input
						id="provider-default-model"
						placeholder="ex: llama3.1"
						value={defaultModel}
						onChange={(e) => setDefaultModel(e.target.value)}
					/>
					<p className="mt-1 text-xs text-foreground-tertiary">
						Utilisé par le chat quand ce provider est le moteur actif.
					</p>
				</div>

				{/* Paramètres techniques — repliés par défaut (mode avancé) */}
				<div className="rounded-lg border border-line-1">
					<button
						type="button"
						className="flex w-full items-center justify-between px-3 py-2 text-sm text-foreground-secondary"
						onClick={() => setAdvancedOpen((v) => !v)}
						aria-expanded={advancedOpen}
					>
						<span>Avancé (paramètres techniques)</span>
						{advancedOpen ? (
							<ChevronDown className="h-4 w-4" />
						) : (
							<ChevronRight className="h-4 w-4" />
						)}
					</button>
					{advancedOpen && (
						<div className="flex flex-col gap-3 border-t border-line-1 px-3 py-3">
							<div>
								<label className="block text-sm font-medium mb-1" htmlFor="provider-api-version">
									api_version {type !== "azure" ? "(Azure uniquement)" : ""}
								</label>
								<Input
									id="provider-api-version"
									placeholder="2023-05-15"
									value={apiVersion}
									disabled={type !== "azure"}
									onChange={(e) => setApiVersion(e.target.value)}
								/>
							</div>
							<div>
								<label className="block text-sm font-medium mb-1" htmlFor="provider-options">
									Options du provider (JSON)
								</label>
								<textarea
									id="provider-options"
									className="h-24 w-full rounded-md border border-line-1 bg-bg-1 px-3 py-2 font-mono text-xs text-foreground"
									placeholder='{"site_name": "Ethan"}'
									value={optionsText}
									onChange={(e) => setOptionsText(e.target.value)}
								/>
								{optionsError && <p className="mt-1 text-xs text-red">{optionsError}</p>}
								<p className="mt-1 text-xs text-foreground-tertiary">
									Options spécifiques au type (ex: OpenRouter routing). Le Core ne les
									renvoie jamais : laisser vide pour conserver l&apos;existant.
								</p>
							</div>
						</div>
					)}
				</div>

				<div className="flex justify-end gap-2 pt-4 border-t border-line-1">
					<Button variant="secondary" size="sm" onClick={onClose}>
						<X className="h-4 w-4" /> Annuler
					</Button>
					<Button size="sm" onClick={handleSubmit} disabled={!canSubmit}>
						<Save className="h-4 w-4" /> {submitLabel}
					</Button>
				</div>
			</div>
		</Dialog>
	);
}


