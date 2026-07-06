"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error("UI Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-3">
            <AlertTriangle size={40} className="text-warning mx-auto" />
            <h2 className="text-lg font-medium text-text">Quelque chose a échoué</h2>
            <p className="text-sm text-text-dim max-w-md">
              {this.state.error?.message || "Erreur inattendue"}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="flex items-center gap-2 mx-auto rounded-lg bg-ethan-600 px-4 py-2 text-white hover:bg-ethan-500 transition-colors"
            >
              <RefreshCw size={14} />
              Réessayer
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}