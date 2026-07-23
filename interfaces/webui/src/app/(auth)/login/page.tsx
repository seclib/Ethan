"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/core/providers/auth-provider";
import { AnimatedBackground } from "./components/animated-background";
import { TopBar } from "./components/top-bar";
import { StatusPanel } from "./components/status-panel";
import { LoginCard } from "./components/login-card";
import { LoginForm } from "./components/login-form";
import { LoadingOverlay } from "./components/loading-overlay";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading: authLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [showOverlay, setShowOverlay] = useState(false);
  const [pendingOperatorId, setPendingOperatorId] = useState<string>("");

  const handleLogin = useCallback(
    async (operatorId: string, password: string) => {
      setError(null);
      setPendingOperatorId(operatorId);
      setShowOverlay(true);
    },
    []
  );

  const handleAuthComplete = useCallback(() => {
    const fakeLogin = async () => {
      try {
        await login("admin@ethan.ai", "password", pendingOperatorId);
        router.push("/");
      } catch (err) {
        setShowOverlay(false);
        setError(err instanceof Error ? err.message : "Authentication failed");
      }
    };
    fakeLogin();
  }, [login, router, pendingOperatorId]);

  const handleAuthError = useCallback((msg: string) => {
    setShowOverlay(false);
    setError(msg);
  }, []);

  return (
    <>
      <AnimatedBackground />
      <TopBar />

      <main className="relative z-10 min-h-screen flex flex-col">
        <div className="flex-1 flex items-center justify-center pt-10">
          <div className="flex w-full max-w-[840px] mx-auto">
            {/* Left: Login card */}
            <div className="flex-1 flex justify-center px-6">
              <LoginCard>
                <LoginForm
                  onSubmit={handleLogin}
                  isLoading={authLoading}
                  error={error}
                />
              </LoginCard>
            </div>

            {/* Right: Status panel */}
            <div className="hidden lg:block">
              <StatusPanel />
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="pb-6 text-center">
          <p className="text-[9px] tracking-[0.15em] text-white/10 font-mono select-none">
            ETHAN Cognitive Operating System v2.4.1 — Authorized Personnel Only
          </p>
          <p className="text-[9px] tracking-[0.15em] text-white/[0.06] font-mono mt-1 select-none">
            Unauthorized access is prohibited and may be prosecuted under applicable law.
          </p>
        </footer>
      </main>

      <LoadingOverlay
        isVisible={showOverlay}
        onComplete={handleAuthComplete}
        onError={handleAuthError}
      />
    </>
  );
}