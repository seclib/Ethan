"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/shared/metric-card";
import { EventStream } from "@/components/shared/event-stream";
import { useFacts } from "@/components/features/memory/hooks/use-memory";
import { useMissions } from "@/components/features/missions/hooks/use-missions";
import { useGoals } from "@/components/features/goals/hooks/use-goals";
import { useFluxEvents } from "@/components/features/flux/hooks/use-flux";
import { useUIStore } from "@/store/ui.store";
import { Search, Download, Eye, RefreshCw, Database, Trash2, Shield, Calendar, Activity, CheckSquare } from "lucide-react";
import type { Fact, Mission, Goal } from "@/types";

export default function WorkspacePage() {
	const [searchQuery, setSearchQuery] = React.useState("");
	const [activeTab, setActiveTab] = React.useState<"memory" | "missions" | "events">("memory");
	const addToast = useUIStore((s) => s.addToast);

	const { facts, isLoading: factsLoading, fetchFacts, deleteFact, isDeleting } = useFacts(
		searchQuery ? { query: searchQuery } : undefined,
	);
	
	const { missions = [], isLoading: missionsLoading, refetch: refetchMissions } = useMissions();
	const { goals = [], isLoading: goalsLoading } = useGoals();
	const { events = [], isLoading: eventsLoading, refetch: refetchEvents } = useFluxEvents();

	const handleDeleteFact = async (fact: Fact) => {
		if (!confirm(`Delete fact "${fact.subject} ${fact.predicate} ${fact.object}"?`)) return;
		const result = await deleteFact(fact.id);
		if (result.error) {
			addToast({ type: "error", message: result.error });
		} else {
			addToast({ type: "success", message: "Fact deleted" });
		}
	};

	const handleSearch = (e: React.FormEvent) => {
		e.preventDefault();
		fetchFacts();
	};

	const totalFacts = facts?.length || 0;
	const categories = [...new Set(facts?.map((f: Fact) => f.category).filter(Boolean))];
	const activeMissions = missions?.filter((m: Mission) => m.status === "running").length || 0;
	const activeGoals = goals?.filter((g: Goal) => g.status === "active").length || 0;

	return (
		<div className="space-y-8 animate-fade-in pb-8">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold tracking-tight text-foreground">Workspace</h1>
					<p className="text-muted-foreground mt-1">Central dashboard for cognitive monitoring, planning, and long-term memory</p>
				</div>
				<div className="flex items-center gap-3">
					<Button variant="outline" size="sm" className="gap-2" onClick={() => {
						fetchFacts();
						refetchMissions();
						refetchEvents();
					}}>
						<RefreshCw size={14} /> Sync Workspace
					</Button>
				</div>
			</div>

			{/* KPI Strip */}
			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<MetricCard title="Memory Facts" value={totalFacts} unit="entries" status="normal" href="#" onClick={() => setActiveTab("memory")} />
				<MetricCard title="Active Missions" value={activeMissions} unit={`/ ${missions?.length || 0}`} status="normal" href="#" onClick={() => setActiveTab("missions")} />
				<MetricCard title="Active Goals" value={activeGoals} unit={`/ ${goals?.length || 0}`} status="normal" href="#" onClick={() => setActiveTab("missions")} />
				<MetricCard title="System Events" value={events?.length || 0} unit="logged" status="normal" href="#" onClick={() => setActiveTab("events")} />
			</div>

			<div className="flex border-b border-border">
				<button
					onClick={() => setActiveTab("memory")}
					className={`px-4 py-2 text-sm font-medium border-b-2 -mb-[2px] transition-colors ${
						activeTab === "memory"
							? "border-primary text-primary"
							: "border-transparent text-muted-foreground hover:text-foreground"
					}`}
				>
					Memory Explorer
				</button>
				<button
					onClick={() => setActiveTab("missions")}
					className={`px-4 py-2 text-sm font-medium border-b-2 -mb-[2px] transition-colors ${
						activeTab === "missions"
							? "border-primary text-primary"
							: "border-transparent text-muted-foreground hover:text-foreground"
					}`}
				>
					Missions & Goals
				</button>
				<button
					onClick={() => setActiveTab("events")}
					className={`px-4 py-2 text-sm font-medium border-b-2 -mb-[2px] transition-colors ${
						activeTab === "events"
							? "border-primary text-primary"
							: "border-transparent text-muted-foreground hover:text-foreground"
					}`}
				>
					System Event Log
				</button>
			</div>

			{activeTab === "memory" ? (
				<div className="space-y-6">
					<form onSubmit={handleSearch} className="flex gap-3">
						<div className="relative flex-1">
							<Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
							<Input
								placeholder="Search memory facts..."
								className="pl-9 bg-elevated"
								value={searchQuery}
								onChange={(e) => setSearchQuery(e.target.value)}
							/>
						</div>
						<Button type="submit" variant="outline">
							Search
						</Button>
					</form>

					{factsLoading ? (
						<div className="space-y-4">
							{[1, 2, 3].map((i) => (
								<Skeleton key={i} variant="rectangle" className="w-full h-12" />
							))}
						</div>
					) : (
						<Card variant="outlined" className="overflow-hidden">
							<div className="overflow-y-auto max-h-[500px]">
								<table className="w-full text-sm">
									<thead className="bg-muted/50 sticky top-0 z-10 border-b">
										<tr>
											<th className="h-10 px-4 text-left font-medium text-muted-foreground w-[120px]">Time</th>
											<th className="h-10 px-4 text-left font-medium text-muted-foreground w-[150px]">Category</th>
											<th className="h-10 px-4 text-left font-medium text-muted-foreground">Content</th>
											<th className="h-10 px-4 text-right font-medium text-muted-foreground w-[100px]">Actions</th>
										</tr>
									</thead>
									<tbody>
										{facts?.map((fact: Fact) => (
											<tr key={fact.id} className="border-b last:border-0 hover:bg-muted/50 transition-colors">
												<td className="p-4 text-muted-foreground font-mono text-xs">
													{new Date(fact.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
												</td>
												<td className="p-4">
													<span className="inline-flex items-center rounded-md bg-accent/10 px-2 py-1 text-xs font-medium text-accent border border-accent/20">
														{fact.category}
													</span>
												</td>
												<td className="p-4">
													<span className="font-semibold text-foreground">{fact.subject}</span>{" "}
													<span className="text-foreground-secondary">{fact.predicate}</span>{" "}
													<span className="text-accent">{fact.object}</span>
												</td>
												<td className="p-4 text-right">
													<div className="flex gap-1 justify-end">
														<Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => addToast({ type: "info", message: `Fact details: ${fact.subject} ${fact.predicate} ${fact.object}` })}>
															<Eye className="h-4 w-4" />
														</Button>
														<Button
															variant="ghost"
															size="sm"
															className="h-8 w-8 p-0 text-destructive"
															onClick={() => handleDeleteFact(fact)}
															disabled={isDeleting}
														>
															<Trash2 className="h-4 w-4" />
														</Button>
													</div>
												</td>
											</tr>
										))}
										{(!facts || facts.length === 0) && (
											<tr>
												<td colSpan={4} className="p-12 text-center text-muted-foreground">
													<Database size={48} className="mx-auto text-muted-foreground/30 mb-4" />
													<p className="mb-2 font-medium">No memory facts recorded</p>
													<p className="text-xs text-muted-foreground/60">System facts will pop up automatically as you interact with the agent</p>
												</td>
											</tr>
										)}
									</tbody>
								</table>
							</div>
						</Card>
					)}
				</div>
			) : activeTab === "missions" ? (
				<div className="grid gap-6 md:grid-cols-2">
					<Card variant="outlined">
						<CardHeader>
							<CardTitle className="text-sm font-semibold uppercase tracking-wider text-foreground-secondary">
								Active Workflow Missions
							</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							{missionsLoading ? (
								<Skeleton variant="rectangle" className="w-full h-32" />
							) : (missions as Mission[]).length > 0 ? (
								(missions as Mission[]).map((mission) => {
									const stepsTotal = mission.steps_total || 0;
									const stepsCompleted = mission.steps_completed || 0;
									const progress = stepsTotal > 0 ? Math.round((stepsCompleted / stepsTotal) * 100) : 0;
									return (
										<div key={mission.id} className="rounded-lg border bg-card p-4 transition-all hover:bg-accent/5">
											<div className="flex items-center justify-between mb-2">
												<div className="font-medium text-foreground">{mission.title}</div>
												<div className="text-xs font-mono text-muted-foreground">{progress}%</div>
											</div>
											<Progress value={progress} className="h-1.5 mb-3" />
											<div className="flex items-center justify-between text-xs text-muted-foreground">
												<span>Steps: {stepsCompleted}/{stepsTotal}</span>
												<span className="capitalize">{mission.status}</span>
											</div>
										</div>
									);
								})
							) : (
								<div className="text-center py-8 text-muted-foreground">
									<Activity size={32} className="mx-auto opacity-30 mb-2" />
									<p className="text-xs">No active missions running</p>
								</div>
							)}
						</CardContent>
					</Card>

					<Card variant="outlined">
						<CardHeader>
							<CardTitle className="text-sm font-semibold uppercase tracking-wider text-foreground-secondary">
								Strategic Planning Goals
							</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							{goalsLoading ? (
								<Skeleton variant="rectangle" className="w-full h-32" />
							) : goals.length > 0 ? (
								goals.map((goal) => (
									<div key={goal.id} className="rounded-lg border bg-card p-4 flex items-center justify-between">
										<div>
											<div className="font-medium text-foreground text-sm">{goal.title}</div>
											<p className="text-xs text-foreground-tertiary mt-1">{goal.description}</p>
										</div>
										<span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
											goal.status === "active" ? "bg-green/10 text-green" : "bg-muted-foreground/10 text-muted-foreground"
										}`}>
											{goal.status}
										</span>
									</div>
								))
							) : (
								<div className="text-center py-8 text-muted-foreground">
									<CheckSquare size={32} className="mx-auto opacity-30 mb-2" />
									<p className="text-xs">No strategic goals defined</p>
								</div>
							)}
						</CardContent>
					</Card>
				</div>
			) : (
				<div className="space-y-4">
					<Card variant="outlined" className="p-4">
						{eventsLoading ? (
							<Skeleton variant="rectangle" className="w-full h-64" />
						) : (
							<EventStream
								events={events || []}
								maxHeight={450}
								showFilters={true}
								onPause={() => {}}
								onResume={() => {}}
							/>
						)}
					</Card>
				</div>
			)}
		</div>
	);
}
