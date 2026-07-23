"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/core/store/ui.store";
import { useMissions } from "@/features/missions/hooks/use-missions";
import type { Mission } from "@/types";
import { X, Target, Play, Pause, Plus } from "lucide-react";

export function MissionControlOverlay() {
  const router = useRouter();
  const { missionControlOpen, setMissionControlOpen } = useUIStore();
  const { missions, isLoading } = useMissions();

  if (!missionControlOpen) return null;

  return (
    <div className="mission-overlay" onClick={() => setMissionControlOpen(false)}>
      <div 
        className="mission-grid" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="col-span-full flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white tracking-wide">Mission Control</h2>
          <div className="flex items-center gap-3">
            <button 
              className="text-white hover:text-accent transition-colors flex items-center gap-2 text-sm bg-white/5 px-3 py-1.5 rounded-md"
              onClick={() => {
                setMissionControlOpen(false);
                router.push("/missions");
              }}
            >
              <Plus size={16} /> New Mission
            </button>
            <button 
              className="text-white hover:text-accent transition-colors"
              onClick={() => setMissionControlOpen(false)}
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="col-span-full text-center text-white/50 py-10">Loading missions...</div>
        ) : missions?.length === 0 ? (
          <div className="col-span-full text-center text-white/50 py-10">No missions found.</div>
        ) : (
          (missions as Mission[]).slice(0, 4).map((mission) => {
            const stepsTotal = mission.steps_total || 1;
            const stepsCompleted = mission.steps_completed || 0;
            const progress = Math.round((stepsCompleted / stepsTotal) * 100);
            
            return (
              <div 
                key={mission.id} 
                className="mission-card"
                onClick={() => {
                  setMissionControlOpen(false);
                  router.push(`/missions?id=${mission.id}`);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 text-white">
                    <Target size={20} className="text-accent" />
                    <h3 className="text-lg font-semibold">{mission.title}</h3>
                  </div>
                  <div className={`text-xs px-2 py-1 rounded-full border ${
                    mission.status === "running" ? "border-green-500/50 text-green-400 bg-green-500/10" :
                    mission.status === "failed" ? "border-red-500/50 text-red-400 bg-red-500/10" :
                    "border-white/20 text-white/70"
                  }`}>
                    {mission.status}
                  </div>
                </div>
                
                <p className="text-sm text-white/60 line-clamp-2 mt-2">
                  {mission.description || "No description provided."}
                </p>

                <div className="mt-auto pt-6">
                  <div className="flex justify-between text-xs text-white/60 mb-2 font-mono">
                    <span>{progress}%</span>
                    <span>{stepsCompleted}/{stepsTotal}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-accent transition-all duration-500" 
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
