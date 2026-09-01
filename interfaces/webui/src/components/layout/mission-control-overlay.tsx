"use client";

/**
 * MissionControlOverlay — vue cockpit temps réel des missions (⌘M, palette).
 *
 * Correctif audit UX (P0-1/P1-1/P1-3) :
 *  - l'ancienne version utilisait des classes CSS inexistantes
 *    (.mission-overlay/.mission-grid/.mission-card) : l'overlay s'affichait
 *    dans le flux de la page, sans fond ni z-index. Toute la mise en forme
 *    est désormais en tokens Tailwind du design system (z-modal, bg-bg-*, …).
 *  - l'overlay s'enregistre dans la pile ESC centralisée (useOverlayStore) :
 *    Escape ferme la couche au sommet, comme Dialog/Popover/FloatingWindow.
 *
 * AGENTS.md : pure présentation — les données viennent du Core (/v1/missions).
 */

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/store/ui.store";
import { useOverlayStore } from "@/store/overlay.store";
import { useMissions } from "@/components/features/missions/hooks/use-missions";
import type { Mission } from "@/types";
import { X, Target, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

export function MissionControlOverlay() {
  const router = useRouter();
  const { missionControlOpen, setMissionControlOpen } = useUIStore();
  const { missions, isLoading } = useMissions();

  const handleClose = React.useCallback(
    () => setMissionControlOpen(false),
    [setMissionControlOpen],
  );

  // Pile ESC centralisée : même contrat que ui/dialog.tsx.
  const handleCloseRef = React.useRef(handleClose);
  handleCloseRef.current = handleClose;
  React.useEffect(() => {
    if (!missionControlOpen) return;
    const unregister = useOverlayStore.getState().push({
      id: "mission-control-overlay",
      onClose: () => handleCloseRef.current(),
    });
    return unregister;
  }, [missionControlOpen]);

  if (!missionControlOpen) return null;

  return (
    <div
      className="fixed inset-0 z-modal flex items-center justify-center p-4 md:p-8"
      role="dialog"
      aria-modal="true"
      aria-label="Mission Control"
      onClick={handleClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" aria-hidden="true" />

      {/* Panneau */}
      <div
        className="relative w-full max-w-5xl max-h-[85vh] overflow-y-auto rounded-2xl border border-line-2 bg-bg-2 shadow-2xl animate-in fade-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-line-1 sticky top-0 bg-bg-2 rounded-t-2xl">
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Target size={18} className="text-accent-400" />
            Mission Control
          </h2>
          <div className="flex items-center gap-2">
            <button
              className="text-foreground-secondary hover:text-foreground transition-colors flex items-center gap-1.5 text-sm rounded-md bg-elevated px-3 py-1.5"
              onClick={() => {
                handleClose();
                router.push("/missions");
              }}
            >
              <Plus size={14} /> New Mission
            </button>
            <button
              className="text-foreground-tertiary hover:text-foreground transition-colors p-1 rounded-md"
              onClick={handleClose}
              aria-label="Fermer Mission Control"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6">

          {isLoading ? (
            <div className="col-span-full text-center text-foreground-tertiary py-10">
              Loading missions...
            </div>
          ) : missions?.length === 0 ? (
            <div className="col-span-full text-center text-foreground-tertiary py-10">
              No missions found.
            </div>
          ) : (
            (missions as Mission[]).slice(0, 4).map((mission) => {
              const stepsTotal = mission.steps_total || 1;
              const stepsCompleted = mission.steps_completed || 0;
              const progress = Math.round((stepsCompleted / stepsTotal) * 100);

              return (
                <button
                  key={mission.id}
                  className="text-left rounded-xl border border-line-1 bg-bg-3 p-4 hover:border-line-2 hover:bg-elevated transition-colors flex flex-col gap-3 min-h-[160px] cursor-pointer"
                  onClick={() => {
                    handleClose();
                    router.push(`/missions?id=${mission.id}`);
                  }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5 text-foreground min-w-0">
                      <Target size={18} className="text-accent-400 shrink-0" />
                      <h3 className="text-sm font-semibold truncate">{mission.title}</h3>
                    </div>
                    <span
                      className={cn(
                        "shrink-0 text-[10px] px-2 py-0.5 rounded-full border",
                        mission.status === "running"
                          ? "border-success/40 text-success bg-success/10"
                          : mission.status === "failed"
                            ? "border-destructive/40 text-destructive bg-destructive/10"
                            : "border-line-2 text-foreground-tertiary",
                      )}
                    >
                      {mission.status}
                    </span>
                  </div>

                  <p className="text-xs text-foreground-tertiary line-clamp-2">
                    {mission.description || "No description provided."}
                  </p>

                  <div className="mt-auto">
                    <div className="flex justify-between text-[10px] text-foreground-tertiary mb-1.5 font-mono">
                      <span>{progress}%</span>
                      <span>{stepsCompleted}/{stepsTotal}</span>
                    </div>
                    <div className="h-1.5 w-full bg-elevated rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent-500 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
