import * as React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/lib/api/models", () => ({
	discoverModels: jest.fn(),
	getInstalledModels: jest.fn(),
	getHardwareInfo: jest.fn(),
	getRuntimesHealth: jest.fn(),
	getDownloads: jest.fn(),
	inspectModel: jest.fn(),
	installModel: jest.fn(),
}));

jest.mock("@/store/model.store", () => ({
	useModelStore: jest.fn((selector: (s: Record<string, unknown>) => unknown) =>
		selector({ selectedModel: "", setSelection: jest.fn() })
	),
}));

jest.mock("next/navigation", () => ({
	useRouter: () => ({ push: jest.fn() }),
}));

import { ModelHub } from "@/components/features/models/components/model-hub";
import {
	discoverModels,
	getDownloads,
	getHardwareInfo,
	getInstalledModels,
	getRuntimesHealth,
} from "@/lib/api/models";

const hubModel = {
	id: "qwen2.5-coder:7b",
	name: "Qwen2.5 Coder 7B",
	provider: "ollama",
	params_b: 7.6,
	description: "Modèle de code.",
	use_case: "coding",
	quantization: "Q4_K_M",
	source: "curated",
	formats_available: ["gguf"],
	is_installed: false,
	compatibility: {
		compatible: true,
		fit_level: "good",
		reason: "",
		recommendation: "",
		recommended_runtime: "ollama",
		supported_runtimes: ["ollama"],
		ram_required_gb: 6,
		vram_required_gb: 0,
		estimated_speed_tps: 20,
		status: "compatible",
		status_label: "Compatible",
		execution_method: "Ollama GGUF",
	},
};

function renderHub() {
	const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
	return render(
		<QueryClientProvider client={queryClient}>
			<ModelHub />
		</QueryClientProvider>
	);
}

describe("ModelHub", () => {
	beforeEach(() => {
		jest.clearAllMocks();
		(getInstalledModels as jest.Mock).mockResolvedValue([]);
		(getHardwareInfo as jest.Mock).mockResolvedValue({
			total_ram_gb: 32,
			available_ram_gb: 20,
			cpu_cores: 8,
			gpu_count: 0,
			gpu_name: "",
			gpu_vram_gb: 0,
			gpu_vram_free_gb: 0,
			backend: "cpu",
			memory_bandwidth_gb_s: 50,
		});
		(getRuntimesHealth as jest.Mock).mockResolvedValue({ status: "healthy", runtimes: {} });
		(getDownloads as jest.Mock).mockResolvedValue([]);
		(discoverModels as jest.Mock).mockResolvedValue([hubModel]);
	});

	it("exposes the local catalog alias in the source filter", async () => {
		renderHub();
		fireEvent.click(await screen.findByRole("button", { name: /Discover/ }));

		const sourceSelect = await screen.findByLabelText("Filtrer par source");
		const values = Array.from(sourceSelect.querySelectorAll("option")).map((o) => o.value);
		expect(values).toEqual(expect.arrayContaining(["all", "curated", "local", "huggingface"]));
	});

	it("discovers and renders models through the Core API", async () => {
		renderHub();
		fireEvent.click(await screen.findByRole("button", { name: /Discover/ }));

		fireEvent.change(await screen.findByPlaceholderText(/Rechercher un modèle/), {
			target: { value: "qwen" },
		});
		fireEvent.click(screen.getByRole("button", { name: /Rechercher/ }));

		expect(await screen.findByText("Qwen2.5 Coder 7B")).toBeTruthy();
		expect(discoverModels).toHaveBeenCalledWith({
			q: "qwen",
			source: "all",
			use_case: undefined,
		});
	});

	it("forwards the use_case filter to the Core", async () => {
		renderHub();
		fireEvent.click(await screen.findByRole("button", { name: /Discover/ }));

		fireEvent.change(await screen.findByLabelText("Filtrer par usage"), {
			target: { value: "coding" },
		});
		fireEvent.click(screen.getByRole("button", { name: /Rechercher/ }));

		await waitFor(() =>
			expect(discoverModels).toHaveBeenCalledWith({
				q: undefined,
				source: "all",
				use_case: "coding",
			})
		);
	});
});