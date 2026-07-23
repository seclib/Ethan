"use client";

import { type FormEvent, useState } from "react";
import { motion } from "framer-motion";

interface LoginFormProps {
  onSubmit: (operatorId: string, password: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function LoginForm({ onSubmit, isLoading, error }: LoginFormProps) {
  const [operatorId, setOperatorId] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(operatorId, password);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Operator ID */}
      <div>
        <label
          htmlFor="operator-id"
          className="block text-[10px] tracking-[0.15em] text-foreground-tertiary uppercase font-mono mb-2"
        >
          Operator ID
        </label>
        <input
          id="operator-id"
          type="text"
          value={operatorId}
          onChange={(e) => setOperatorId(e.target.value)}
          placeholder="Enter operator identifier"
          required
          autoComplete="username"
          spellCheck={false}
          className="w-full h-10 px-3 bg-surface border border-line-2 rounded text-[13px] text-foreground placeholder:text-foreground-tertiary font-mono outline-none transition-colors focus:border-accent focus:bg-surface-hover"
        />
      </div>

      {/* Password */}
      <div>
        <label
          htmlFor="password"
          className="block text-[10px] tracking-[0.15em] text-foreground-tertiary uppercase font-mono mb-2"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          required
          autoComplete="current-password"
          className="w-full h-10 px-3 bg-surface border border-line-2 rounded text-[13px] text-foreground placeholder:text-foreground-tertiary font-mono outline-none transition-colors focus:border-accent focus:bg-surface-hover"
        />
      </div>

      {/* Remember device + Forgot */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className="w-3 h-3 rounded border border-line-2 bg-surface accent-accent"
          />
          <span className="text-[10px] tracking-[0.05em] text-foreground-tertiary font-mono">
            Remember device
          </span>
        </label>
        <button
          type="button"
          className="text-[10px] tracking-[0.05em] text-foreground-tertiary font-mono hover:text-foreground-secondary transition-colors"
        >
          Forgot credentials
        </button>
      </div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="py-2 px-3 bg-red-soft border border-red/20 rounded"
        >
          <p className="text-[11px] font-mono text-red/80">
            ACCESS DENIED — {error}
          </p>
        </motion.div>
      )}

      {/* Submit button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full h-10 bg-surface border border-line-2 rounded text-[11px] tracking-[0.2em] uppercase font-semibold text-foreground-secondary transition-all duration-150 hover:bg-surface-hover hover:border-line-3 hover:text-foreground active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-surface disabled:hover:border-line-2 disabled:hover:text-foreground-secondary disabled:hover:scale-100"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-3.5 w-3.5 text-accent"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Authenticating
          </span>
        ) : (
          "Login"
        )}
      </button>
    </form>
  );
}