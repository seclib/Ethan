"use client";

/**
 * useModelHub — Hook for Model Hub discovery, inspection, and installation.
 *
 * Source unique : ETHAN Core via the Model Hub API endpoints.
 * No business logic — only API calls and state management.
 */

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
	discoverModels,
	getInstalledModels,
	getHardwareInfo,
	getRuntimesHealth,
	inspectModel,
	installModel,
	getDownloads,
	type HubModel,
	type InstalledModel,
	type HardwareInfo,
	type RuntimeHealth,
	type ModelInspection,
	type DownloadItem,
} from "@/lib/api/models";

const HUB_INSTALLED_KEY = ["model-hub", "installed"] as const;
const HUB_HARDWARE_KEY = ["model-hub", "hardware"] as const;
const HUB_RUNTIMES_KEY = ["model-hub", "runtimes"] as const;
const HUB_DOWNLOADS_KEY = ["model-hub", "downloads"] as const;

export function useModelHub() {
	const queryClient = useQueryClient();
	const [discoverQuery, setDiscoverQuery] = useState("");
	const [discoverSource, setDiscoverSource] = useState<string>("all");
	const [discoverUseCase, setDiscoverUseCase] = useState<string>("");
	const [discoverResults, setDiscoverResults] = useState<HubModel[]>([]);
	const [isDiscovering, setIsDiscovering] = useState(false);
	const [discoverError, setDiscoverError] = useState<string | null>(null);

	// Installed models
	const {
		data: installed = [],
		isLoading: installedLoading,
		error: installedErrorObj,
		refetch: refetchInstalled,
	} = useQuery<InstalledModel[]>({
		queryKey: HUB_INSTALLED_KEY,
		queryFn: () => getInstalledModels(),
		staleTime: 30_000,
	});

	// Hardware info
	const {
		data: hardware,
		isLoading: hardwareLoading,
	} = useQuery<HardwareInfo>({
		queryKey: HUB_HARDWARE_KEY,
		queryFn: () => getHardwareInfo(),
		staleTime: 60_000,
	});

	// Runtime health
	const {
		data: runtimeHealth,
		isLoading: runtimesLoading,
		refetch: refetchRuntimes,
	} = useQuery<RuntimeHealth>({
		queryKey: HUB_RUNTIMES_KEY,
		queryFn: () => getRuntimesHealth(),
		staleTime: 30_000,
	});

	// Downloads tracking
	const {
		data: downloads = [],
		isLoading: downloadsLoading,
		refetch: refetchDownloads,
	} = useQuery<DownloadItem[]>({
		queryKey: HUB_DOWNLOADS_KEY,
		queryFn: () => getDownloads(),
		refetchInterval: (query) => {
			const hasActive = (query.state.data || []).some(
				(d) => d.status === "starting" || d.status === "downloading",
			);
			return hasActive ? 3_000 : 30_000;
		},
	});

	// Discover models (manual trigger — not auto-fetched)
	const handleDiscover = useCallback(async (query?: string, source?: string, useCase?: string) => {
		const q = query ?? discoverQuery;
		const s = source ?? discoverSource;
		const u = useCase ?? discoverUseCase;
		setIsDiscovering(true);
		setDiscoverError(null);
		try {
			const results = await discoverModels({ q: q || undefined, source: s || undefined, use_case: u || undefined });
			setDiscoverResults(results);
		} catch (err: unknown) {
			setDiscoverError(err instanceof Error ? err.message : "Discovery failed");
			setDiscoverResults([]);
		} finally {
			setIsDiscovering(false);
		}
	}, [discoverQuery, discoverSource, discoverUseCase]);

	// Install model (mutation)
	const installMutation = useMutation({
		mutationFn: (payload: { model: string; provider?: string }) => installModel(payload),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: HUB_INSTALLED_KEY });
			queryClient.invalidateQueries({ queryKey: HUB_DOWNLOADS_KEY });
		},
	});

	// Inspect model
	const [inspection, setInspection] = useState<ModelInspection | null>(null);
	const [isInspecting, setIsInspecting] = useState(false);

	const handleInspect = useCallback(async (modelId: string) => {
		setIsInspecting(true);
		try {
			const result = await inspectModel(modelId);
			setInspection(result);
			return result;
		} catch {
			setInspection(null);
			return null;
		} finally {
			setIsInspecting(false);
		}
	}, []);

	return {
		// Installed
		installed,
		installedLoading,
		installedError: installedErrorObj?.message ?? null,
		refetchInstalled,

		// Hardware
		hardware,
		hardwareLoading,

		// Runtimes
		runtimeHealth,
		runtimesLoading,
		refetchRuntimes,

		// Downloads
		downloads,
		downloadsLoading,
		refetchDownloads,

		// Discover
		discoverQuery,
		setDiscoverQuery,
		discoverSource,
		setDiscoverSource,
		discoverUseCase,
		setDiscoverUseCase,
		discoverResults,
		isDiscovering,
		discoverError,
		handleDiscover,

		// Install
		installModel: installMutation.mutateAsync,
		isInstalling: installMutation.isPending,
		installError: installMutation.error?.message ?? null,

		// Inspect
		inspection,
		isInspecting,
		handleInspect,
	};
}
