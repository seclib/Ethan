"use client";

import * as React from "react";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Diagnostic local, sans données sensibles.
    console.error("[ETHAN][ErrorBoundary]", error, info.componentStack);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      this.props.fallback ?? (
        <div className="rounded-xl border border-line-1 bg-bg-1 p-4 text-sm text-foreground-secondary">
          <p className="font-medium text-foreground">Un composant secondaire n'a pas pu s'afficher.</p>
          <p className="mt-1 text-xs text-foreground-tertiary">
            Les données principales restent disponibles. Réessayez l'affichage si nécessaire.
          </p>
          <button
            type="button"
            onClick={this.reset}
            className="mt-3 rounded-lg border border-line-1 px-3 py-1.5 text-xs hover:bg-elevated"
          >
            Réessayer
          </button>
        </div>
      )
    );
  }
}
