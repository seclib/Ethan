"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface LoadingOverlayProps {
  isVisible: boolean;
  onComplete: () => void;
  onError: (error: string) => void;
}

const AUTH_STEPS = [
  { label: "Verifying credentials", duration: 600 },
  { label: "Establishing encrypted tunnel", duration: 800 },
  { label: "Validating hardware fingerprint", duration: 700 },
  { label: "Synchronizing memory", duration: 900 },
  { label: "Loading cognitive modules", duration: 750 },
  { label: "Initializing runtime", duration: 500 },
];

export function LoadingOverlay({ isVisible, onComplete, onError }: LoadingOverlayProps) {
  const [currentStep, setCurrentStep] = useState(-1);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"authenticating" | "granted" | "failed">("authenticating");
  const cancelledRef = useRef(false);

  // Reset state when overlay becomes visible
  useEffect(() => {
    if (isVisible) {
      setCurrentStep(-1);
      setProgress(0);
      setStatus("authenticating");
      cancelledRef.current = false;
    }
  }, [isVisible]);

  // Animate through steps
  useEffect(() => {
    if (!isVisible || status !== "authenticating") return;

    let stepIndex = 0;

    const runStep = () => {
      if (cancelledRef.current || stepIndex >= AUTH_STEPS.length) return;

      setCurrentStep(stepIndex);

      const step = AUTH_STEPS[stepIndex];
      const startProgress = (stepIndex / AUTH_STEPS.length) * 100;
      const endProgress = ((stepIndex + 1) / AUTH_STEPS.length) * 100;
      const stepDuration = step.duration;

      // Animate progress bar for this step
      const stepStart = performance.now();
      const animateProgress = (now: number) => {
        if (cancelledRef.current) return;
        const elapsed = now - stepStart;
        const t = Math.min(elapsed / stepDuration, 1);
        // Ease-in-out for smooth progress
        const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        setProgress(startProgress + (endProgress - startProgress) * eased);

        if (t < 1) {
          requestAnimationFrame(animateProgress);
        } else {
          stepIndex++;
          if (stepIndex >= AUTH_STEPS.length) {
            setProgress(100);
            setStatus("granted");
            // Small delay before triggering completion
            setTimeout(() => {
              if (!cancelledRef.current) onComplete();
            }, 1200);
          } else {
            setTimeout(runStep, 150);
          }
        }
      };
      requestAnimationFrame(animateProgress);
    };

    // Initial delay before first step
    const initialDelay = setTimeout(runStep, 400);

    return () => {
      clearTimeout(initialDelay);
    };
  }, [isVisible, status, onComplete, onError]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#07090d]/95 backdrop-blur-sm"
        >
          <div className="w-full max-w-[420px] px-6">
            {/* Status title */}
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.4 }}
              className="text-center mb-10"
            >
              <p className="text-[10px] tracking-[0.25em] text-cyan-400/60 uppercase font-mono">
                {status === "granted"
                  ? "ACCESS GRANTED"
                  : status === "failed"
                  ? "AUTHENTICATION FAILED"
                  : "AUTHENTICATING"}
              </p>
            </motion.div>

            {/* Progress bar */}
            {status === "authenticating" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="mb-8"
              >
                <div className="h-px bg-white/5 w-full overflow-hidden rounded-full">
                  <motion.div
                    className="h-full bg-cyan-400/50"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </motion.div>
            )}

            {/* Grant animation */}
            {status === "granted" && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="flex justify-center mb-8"
              >
                <div className="w-12 h-12 rounded-full border border-emerald-400/30 bg-emerald-400/5 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-emerald-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </motion.div>
            )}

            {/* Steps list */}
            <div className="space-y-2">
              {AUTH_STEPS.map((step, i) => {
                const isActive = currentStep === i;
                const isDone = currentStep > i || status === "granted";
                const isCurrent = currentStep === i;

                return (
                  <motion.div
                    key={step.label}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{
                      opacity: isDone || isActive ? 1 : 0.25,
                      x: 0,
                    }}
                    transition={{ delay: i * 0.08, duration: 0.3 }}
                    className="flex items-center gap-3 py-1.5"
                  >
                    {/* Status icon */}
                    <span className="w-4 flex justify-center">
                      {isDone ? (
                        <svg
                          className="w-3 h-3 text-emerald-400/70"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : isCurrent && status === "authenticating" ? (
                        <span className="block w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.5)] animate-pulse" />
                      ) : (
                        <span className="block w-1.5 h-1.5 rounded-full bg-white/10" />
                      )}
                    </span>

                    {/* Label */}
                    <span
                      className={`text-[11px] font-mono tracking-[0.05em] transition-colors ${
                        isDone
                          ? "text-white/40"
                          : isCurrent
                          ? "text-white/70"
                          : "text-white/15"
                      }`}
                    >
                      {step.label}
                      {isCurrent && status === "authenticating" && (
                        <span className="inline-flex ml-1">
                          <span className="animate-pulse">.</span>
                          <span className="animate-pulse" style={{ animationDelay: "0.2s" }}>.</span>
                          <span className="animate-pulse" style={{ animationDelay: "0.4s" }}>.</span>
                        </span>
                      )}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
