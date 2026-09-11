/**
 * Tests du dialogue de restauration de la corbeille.
 *
 * Le dialogue est passif : il transmet les intents utilisateur (restaurer,
 * vider, archiver) aux fonctions API mockées. Aucune logique métier n'est
 * testée ici — elle appartient au Core.
 */
import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RestoreDialog } from "../../../src/components/features/folders/components/restore-dialog";
import * as foldersApi from "../../../src/lib/api/folders";

// Mock du module API
jest.mock("../../../src/lib/api/folders", () => ({
	...jest.requireActual("../../../src/lib/api/folders"),
	listDeletedItems: jest.fn(),
	restoreDeletedItem: jest.fn(),
	emptyTrash: jest.fn(),
	createArchive: jest.fn(),
}));

// Mock du query client de TanStack
jest.mock("@tanstack/react-query", () => ({
	...jest.requireActual("@tanstack/react-query"),
	useQueryClient: () => ({
		invalidateQueries: jest.fn(),
	}),
	useQuery: jest.fn(),
	useMutation: jest.fn(),
}));

const mockQuery = foldersApi.listDeletedItems as jest.MockedFunction<typeof foldersApi.listDeletedItems>;
const mockRestore = foldersApi.restoreDeletedItem as jest.MockedFunction<typeof foldersApi.restoreDeletedItem>;
const mockEmpty = foldersApi.emptyTrash as jest.MockedFunction<typeof foldersApi.emptyTrash>;
const mockArchive = foldersApi.createArchive as jest.MockedFunction<typeof foldersApi.createArchive>;

const sampleItems: foldersApi.DeletedItem[] = [
	{ id: "d1", type: "folder", name: "Projet Financier", deleted_at: "2025-01-15T10:00:00Z", deleted_by: "alice" },
	{ id: "d2", type: "resource", name: "rapport.pdf", deleted_at: "2025-01-16T12:00:00Z", deleted_by: "alice" },
];

describe("RestoreDialog — corbeille", () => {
	beforeEach(() => {
		jest.clearAllMocks();
	});

	it("affiche un loader pendant le chargement", () => {
		require("@tanstack/react-query").useQuery.mockReturnValue({
			data: undefined,
			isLoading: true,
			isError: false,
		});
		require("@tanstack/react-query").useMutation.mockReturnValue({
			mutateAsync: jest.fn(),
			isPending: false,
		});

		render(<RestoreDialog open={true} onOpenChange={jest.fn()} />);
		expect(screen.getByText(/Chargement de la corbeille/)).toBeInTheDocument();
	});

	it("affiche un message vide quand la corbeille est vide", () => {
		require("@tanstack/react-query").useQuery.mockReturnValue({
			data: [],
			isLoading: false,
			isError: false,
		});
		require("@tanstack/react-query").useMutation.mockReturnValue({
			mutateAsync: jest.fn(),
			isPending: false,
		});

		render(<RestoreDialog open={true} onOpenChange={jest.fn()} />);
		expect(screen.getByText(/La corbeille est vide/)).toBeInTheDocument();
	});

	it("liste les éléments supprimés avec leurs métadonnées", () => {
		require("@tanstack/react-query").useQuery.mockReturnValue({
			data: sampleItems,
			isLoading: false,
			isError: false,
		});
		require("@tanstack/react-query").useMutation.mockReturnValue({
			mutateAsync: jest.fn(),
			isPending: false,
		});

		render(<RestoreDialog open={true} onOpenChange={jest.fn()} />);
		expect(screen.getByText("Projet Financier")).toBeInTheDocument();
		expect(screen.getByText("rapport.pdf")).toBeInTheDocument();
		expect(screen.getAllByText("folder")[0]).toBeInTheDocument();
		expect(screen.getAllByText("resource")[0]).toBeInTheDocument();
	});

	it("restaure un élément via le bouton Restaurer", async () => {
		require("@tanstack/react-query").useQuery.mockReturnValue({
			data: sampleItems,
			isLoading: false,
			isError: false,
		});
		// Les 3 useMutation sont résolus dans l'ordre : restore, empty, archive.
		// On branche chaque mutateAsync sur l'API mockée correspondante.
		require("@tanstack/react-query").useMutation
			.mockReturnValueOnce({ mutateAsync: (...args: unknown[]) => mockRestore(...args), isPending: false })
			.mockReturnValueOnce({ mutateAsync: (...args: unknown[]) => mockEmpty(...args), isPending: false })
			.mockReturnValue({ mutateAsync: (...args: unknown[]) => mockArchive(...args), isPending: false });

		render(<RestoreDialog open={true} onOpenChange={jest.fn()} />);

		fireEvent.click(screen.getAllByRole("button", { name: /Restaurer/ })[0]);

		await waitFor(() => {
			expect(mockRestore).toHaveBeenCalledWith("d1");
		});
	});

	it("vide la corbeille via le bouton Vider la corbeille", async () => {
		require("@tanstack/react-query").useQuery.mockReturnValue({
			data: sampleItems,
			isLoading: false,
			isError: false,
		});
		require("@tanstack/react-query").useMutation
			.mockReturnValueOnce({ mutateAsync: (...args: unknown[]) => mockRestore(...args), isPending: false })
			.mockReturnValueOnce({ mutateAsync: (...args: unknown[]) => mockEmpty(...args), isPending: false })
			.mockReturnValue({ mutateAsync: (...args: unknown[]) => mockArchive(...args), isPending: false });

		render(<RestoreDialog open={true} onOpenChange={jest.fn()} />);

		// Simuler la confirmation du navigateur
		jest.spyOn(window, "confirm").mockReturnValue(true);

		fireEvent.click(screen.getByRole("button", { name: /Vider la corbeille/ }));

		await waitFor(() => {
			expect(mockEmpty).toHaveBeenCalled();
		});
	});

	it("désactive les boutons pendant qu'une action est en cours", () => {
		require("@tanstack/react-query").useQuery.mockReturnValue({
			data: sampleItems,
			isLoading: false,
			isError: false,
		});
		require("@tanstack/react-query").useMutation
			.mockReturnValue({ mutateAsync: jest.fn(), isPending: true });

		render(<RestoreDialog open={true} onOpenChange={jest.fn()} />);

		// Le bouton "Vider la corbeille" devrait être désactivé car isPending=true
		expect(screen.getByRole("button", { name: /Vidage…/ })).toBeInTheDocument();
	});
});