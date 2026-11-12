/**
 * Tests WebUI — ModelSelector (chat).
 *
 * `useActiveModel` et `useModels` sont mockés : ces tests valident le rendu du
 * sélecteur (déclencheur, listbox groupée, recherche, épinglage) et les
 * invariants UI : un modèle déclaré indisponible par le Core n'est pas
 * sélectionnable, épinger ne sélectionne jamais.
 */

import { render, screen, fireEvent, within } from "@testing-library/react";

import { ModelSelector } from "@/components/shared/model-selector";
import { useActiveModel } from "@/components/features/assistant/hooks/use-active-model";
import { useModels } from "@/components/features/providers/hooks/use-models";
import type { ModelInfo } from "@/lib/api/models";
import type { Provider } from "@/lib/api/providers";

jest.mock("@/components/features/assistant/hooks/use-active-model", () => ({
	useActiveModel: jest.fn(),
}));
jest.mock("@/components/features/providers/hooks/use-models", () => ({
	useModels: jest.fn(),
}));

const setProvider = jest.fn();
const setModel = jest.fn();
const pinModel = jest.fn();
const unpinModel = jest.fn();

const ollamaProvider: Provider = {
	id: "ollama",
	name: "Ollama",
	type: "ollama",
	enabled: true,
	status: "connected",
	default_model: "llama3.2",
	is_default: true,
	base_url: "http://host:11434",
	models: [],
};

function makeModel(over: Partial<ModelInfo> = {}): ModelInfo {
	return {
		id: "llama3.2",
		name: "Llama 3.2",
		model: "llama3.2",
		provider: "ollama",
		context_length: 131072,
		is_local: true,
		is_private: true,
		quality_score: 0.8,
		capabilities: ["chat"],
		is_available: true,
		is_custom: false,
		source: "discovered",
		...over,
	};
}

const defaultModels: ModelInfo[] = [
	makeModel(),
	makeModel({
		id: "qwen2.5-coder",
		name: "Qwen 2.5 Coder",
		model: "qwen2.5-coder",
		is_available: false,
	}),
	makeModel({
		id: "gpt-4o",
		name: "GPT-4o",
		model: "gpt-4o",
		provider: "openai",
		is_local: false,
	}),
];

interface SetupOpts {
	models?: ModelInfo[];
	isLoading?: boolean;
	selectedModel?: string;
	activeProvider?: Provider | null;
	isPinned?: (providerId: string, modelId: string) => boolean;
}

let searchModels: jest.Mock;

function setup(opts: SetupOpts = {}) {
	const models = opts.models ?? defaultModels;
	(useActiveModel as jest.Mock).mockReturnValue({
		activeProvider: opts.activeProvider ?? ollamaProvider,
		selectedModel: opts.selectedModel ?? "llama3.2",
		setProvider,
		setModel,
		enabledProviders: [ollamaProvider],
	});
	searchModels = jest.fn((query: string) => {
		const q = query.toLowerCase().trim();
		if (!q) return models;
		return models.filter((m) =>
			[m.name, m.model, m.provider].some((value) => value.toLowerCase().includes(q)),
		);
	});
	(useModels as jest.Mock).mockReturnValue({
		pinned: [],
		pinModel,
		unpinModel,
		isPinned: opts.isPinned ?? (() => false),
		searchModels,
		isLoading: opts.isLoading ?? false,
	});
}

function openDropdown() {
	fireEvent.click(screen.getByRole("button", { name: /Ollama \/ llama3\.2/ }));
	expect(screen.getByRole("listbox")).toBeInTheDocument();
}

beforeEach(() => {
	jest.clearAllMocks();
});

describe("ModelSelector — déclencheur et sélection", () => {
	it("affiche le provider actif et le modèle sélectionné", () => {
		setup();
		render(<ModelSelector />);
		expect(
			screen.getByRole("button", { name: /Ollama \/ llama3\.2/ }),
		).toBeInTheDocument();
	});

	it("ouvre la listbox et propose tous les modèles du catalogue", () => {
		setup();
		render(<ModelSelector />);
		openDropdown();
		expect(screen.getAllByRole("option")).toHaveLength(3);
	});

	it("sélection : setProvider + setModel puis fermeture", () => {
		setup();
		render(<ModelSelector />);
		openDropdown();
		fireEvent.click(screen.getByText("Llama 3.2"));
		expect(setProvider).toHaveBeenCalledWith("ollama");
		expect(setModel).toHaveBeenCalledWith("llama3.2");
		expect(screen.queryByRole("listbox")).toBeNull();
	});

	it("modèle sélectionné marqué aria-selected", () => {
		setup();
		render(<ModelSelector />);
		openDropdown();
		const option = screen.getByText("Llama 3.2").closest("[role='option']");
		expect(option).toHaveAttribute("aria-selected", "true");
	});
});

describe("ModelSelector — modèle indisponible (Core)", () => {
	it("grisé, non sélectionnable, mais épinglable", () => {
		setup();
		render(<ModelSelector />);
		openDropdown();
		const option = screen
			.getByText("Qwen 2.5 Coder")
			.closest("[role='option']") as HTMLElement;
		expect(option).toHaveAttribute("aria-disabled", "true");
		expect(within(option).getByText("Indisponible")).toBeInTheDocument();
		fireEvent.click(option);
		expect(setProvider).not.toHaveBeenCalled();
		expect(setModel).not.toHaveBeenCalled();
	});
});

describe("ModelSelector — épinglage", () => {
	it("épingler n'a jamais sélectionné le modèle", () => {
		setup();
		render(<ModelSelector />);
		openDropdown();
		const option = screen.getByText("Llama 3.2").closest("[role='option']") as HTMLElement;
		fireEvent.click(within(option).getByRole("button", { name: "Épingler le modèle" }));
		expect(pinModel).toHaveBeenCalledWith("ollama", "llama3.2");
		expect(setProvider).not.toHaveBeenCalled();
	});

	it("modèle épinglé → désépinglage", () => {
		setup({ isPinned: () => true });
		render(<ModelSelector />);
		openDropdown();
		const option = screen.getByText("Llama 3.2").closest("[role='option']") as HTMLElement;
		fireEvent.click(within(option).getByRole("button", { name: "Désépingler le modèle" }));
		expect(unpinModel).toHaveBeenCalledWith("ollama", "llama3.2");
	});
});

describe("ModelSelector — recherche et états", () => {
	it("recherche filtrée puis aucun résultat", () => {
		setup();
		render(<ModelSelector />);
		openDropdown();
		const input = screen.getByPlaceholderText("Search models...");
		fireEvent.change(input, { target: { value: "gpt" } });
		expect(searchModels).toHaveBeenCalledWith("gpt");
		expect(screen.getByText("GPT-4o")).toBeInTheDocument();
		expect(screen.queryByText("Llama 3.2")).toBeNull();
		fireEvent.change(input, { target: { value: "zzzz" } });
		expect(screen.getByText("Aucun modèle pour « zzzz »")).toBeInTheDocument();
	});

	it("catalogue vide", () => {
		setup({ models: [] });
		render(<ModelSelector />);
		openDropdown();
		expect(screen.getByText("Aucun modèle disponible")).toBeInTheDocument();
	});

	it("chargement du catalogue Core", () => {
		setup({ models: [], isLoading: true });
		render(<ModelSelector />);
		openDropdown();
		expect(screen.getByText("Chargement des modèles…")).toBeInTheDocument();
	});
});

