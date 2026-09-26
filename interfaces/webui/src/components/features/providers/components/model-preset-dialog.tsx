"use client";

/**
 * ModelPresetDialog — Création / édition d'une fiche modèle custom.
 *
 * Une fiche custom est le SEUL objet modèle configurable côté Core
 * (`core/llm/model_store.py` → POST/PUT /models) : elle référence un modèle
 * de base et porte des paramètres avancés (params). Les modèles découverts
 * auprès d'un provider ne sont pas éditables localement — leur état est géré
 * par le provider.
 *
 * Les paramètres techniques (JSON `params`) sont repliés par défaut : l'UX
 * principale ne montre que nom / modèle technique / activation.
 */

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { ModelInfo } from "@/lib/api/models";
import { ChevronDown, ChevronRight, Save, X } from "lucide-react";

export interface ModelPresetPayload {
	name: string;
	model: string;
	base_model_id: string;
	params: Record<string, unknown>;
	is_active: boolean;
}

interface Props {
	open: boolean;
	/** Fiche existante à éditer (null = création, éventuellement pré-remplie). */
	model: ModelInfo | null;
	/** Modèle découvert servant de base à un nouveau preset. */
	basedOn: ModelInfo | null;
	onClose: () => void;
	onSubmit: (payload: ModelPresetPayload) => Promise<void>;
}

function parseJsonObject(text: string): { value?: Record<string, unknown>; error?: string } {
	const trimmed = text.trim();
	if (!trimmed) return { value: {} };
	try {
		const parsed = JSON.parse(trimmed);
		if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
			return { error: "Les paramètres doivent être un objet JSON." };
		}
		return { value: parsed as Record<string, unknown> };
	} catch {
		return { error: "JSON invalide." };
	}
}

export function ModelPresetDialog({ open, model, basedOn, onClose, onSubmit }: Props) {
	const [name, setName] = React.useState("");
	const [technicalModel, setTechnicalModel] = React.useState("");
	const [baseModelId, setBaseModelId] = React.useState("");
	const [isActive, setIsActive] = React.useState(true);
	const [paramsText, setParamsText] = React.useState("{}");
	const [paramsError, setParamsError] = React.useState<string | null>(null);
	const [advancedOpen, setAdvancedOpen] = React.useState(false);

	const source = model ?? basedOn;

	React.useEffect(() => {
		if (!open) return;
		setParamsError(null);
		setAdvancedOpen(false);
		if (model) {
			setName(model.name ?? "");
			setTechnicalModel(model.model ?? "");
			setBaseModelId(model.base_model_id ?? "");
			setIsActive(model.is_available);
			setParamsText(JSON.stringify(model.params ?? {}, null, 2));
		} else {
			setName(basedOn ? `${basedOn.name} (preset)` : "");
			setTechnicalModel(basedOn?.model ?? "");
			setBaseModelId(basedOn?.model ?? "");
			setIsActive(true);
			setParamsText("{}");
		}
	}, [open, model, basedOn]);

	const handleSubmit = async () => {
		const parsed = parseJsonObject(paramsText);
		if (parsed.error) {
			setParamsError(parsed.error);
			return;
		}
		setParamsError(null);
		await onSubmit({
			name: name.trim(),
			model: technicalModel.trim(),
			base_model_id: baseModelId.trim(),
			params: parsed.value ?? {},
			is_active: isActive,
		});
		onClose();
	};

	const title = model ? "Configurer le modèle (fiche custom)" : "Créer un preset de modèle";

	return (
		<Dialog open={open} onClose={onClose} title={title} size="md">
			<div className="flex flex-col gap-4">
				{source && (
					<p className="text-xs text-foreground-tertiary">
						Modèle de base : <span className="font-mono">{source.model}</span>
						{source.provider ? ` · ${source.provider}` : ""} (métadonnées ETHAN Core)
					</p>
				)}

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="preset-name">
						Nom de la fiche
					</label>
					<Input
						id="preset-name"
						placeholder="ex: Llama 3.1 — créatif"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="preset-model">
						Identifiant technique transmis au provider
					</label>
					<Input
						id="preset-model"
						placeholder="ex: llama3.1"
						value={technicalModel}
						onChange={(e) => setTechnicalModel(e.target.value)}
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1" htmlFor="preset-base">
						Modèle de base (référence Core)
					</label>
					<Input
						id="preset-base"
						placeholder="ex: llama3.1"
						value={baseModelId}
						onChange={(e) => setBaseModelId(e.target.value)}
					/>
				</div>

				<label className="flex items-center gap-2 text-sm text-foreground-secondary">
					<input
						type="checkbox"
						checked={isActive}
						onChange={(e) => setIsActive(e.target.checked)}
					/>
					Fiche active (utilisable par la sélection Core)
				</label>

				<div className="rounded-lg border border-line-1">
					<button
						type="button"
						className="flex w-full items-center justify-between px-3 py-2 text-sm text-foreground-secondary"
						onClick={() => setAdvancedOpen((v) => !v)}
						aria-expanded={advancedOpen}
					>
						<span>Avancé (paramètres de génération)</span>
						{advancedOpen ? (
							<ChevronDown className="h-4 w-4" />
						) : (
							<ChevronRight className="h-4 w-4" />
						)}
					</button>
					{advancedOpen && (
						<div className="flex flex-col gap-2 border-t border-line-1 px-3 py-3">
							<label className="block text-sm font-medium" htmlFor="preset-params">
								params (JSON)
							</label>
							<textarea
								id="preset-params"
								className="h-28 w-full rounded-md border border-line-1 bg-bg-1 px-3 py-2 font-mono text-xs text-foreground"
								placeholder='{"temperature": 0.7, "max_tokens": 2048}'
								value={paramsText}
								onChange={(e) => setParamsText(e.target.value)}
							/>
							{paramsError && <p className="text-xs text-red">{paramsError}</p>}
							<p className="text-xs text-foreground-tertiary">
								Paramètres transmis par ETHAN Core lors de la génération
								(temperature, top_p, max_tokens, context_length…).
							</p>
						</div>
					)}
				</div>

				<div className="flex justify-end gap-2 pt-4 border-t border-line-1">
					<Button variant="secondary" size="sm" onClick={onClose}>
						<X className="h-4 w-4" /> Annuler
					</Button>
					<Button
						size="sm"
						onClick={handleSubmit}
						disabled={!name.trim() || !technicalModel.trim()}
					>
						<Save className="h-4 w-4" /> {model ? "Enregistrer" : "Créer"}
					</Button>
				</div>
			</div>
		</Dialog>
	);
}

