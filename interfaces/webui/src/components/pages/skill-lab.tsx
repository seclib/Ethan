"use client";

import { useState } from "react";
import { api, type SkillTestResult } from "@/lib/api";
import { FlaskConical, Play, CheckCircle, XCircle } from "lucide-react";

export function SkillLabPage() {
  const [name, setName] = useState("mon_skill");
  const [code, setCode] = useState("print('Hello from skill')\nresult = {'status': 'ok'}");
  const [testInput, setTestInput] = useState("");
  const [requirements, setRequirements] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SkillTestResult | null>(null);
  const [results, setResults] = useState<SkillTestResult[]>([]);
  const [showResults, setShowResults] = useState(false);

  const runTest = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await api.testSkill(
        name,
        code,
        testInput,
        requirements.split(",").map((r) => r.trim()).filter(Boolean)
      );
      setResult(res);
    } catch (e) {
      setResult({
        id: "error",
        skill_name: name,
        status: "error",
        passed: false,
        duration_ms: 0,
        output: "",
        error: (e as Error).message,
      });
    }
    setLoading(false);
  };

  const loadResults = async () => {
    try {
      setResults(await api.getSkillResults());
    } catch {}
    setShowResults(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text">Skill Lab</h1>
        <p className="text-text-dim text-sm mt-1">Sandbox de test et validation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test form */}
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-surface-2 p-4">
            <h3 className="font-medium text-text mb-3">Tester un skill</h3>
            <div className="space-y-3">
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nom du skill"
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
              />
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={8}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm font-mono text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
              />
              <input
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                placeholder="Entrée de test (optionnel)"
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
              />
              <input
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="Dépendances pip (séparées par ,)"
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
              />
              <button
                onClick={runTest}
                disabled={loading || !code}
                className="flex items-center gap-2 rounded-lg bg-ethan-600 px-4 py-2 text-white hover:bg-ethan-500 disabled:opacity-50 transition-colors"
              >
                <Play size={14} />
                {loading ? "Test en cours..." : "Lancer le test"}
              </button>
            </div>
          </div>

          {result && (
            <div
              className={`rounded-lg border p-4 ${
                result.passed
                  ? "border-green-500/30 bg-green-500/10"
                  : "border-red-500/30 bg-red-500/10"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                {result.passed ? (
                  <CheckCircle size={18} className="text-green-400" />
                ) : (
                  <XCircle size={18} className="text-red-400" />
                )}
                <span className={result.passed ? "text-green-400" : "text-red-400"}>
                  {result.passed ? "Réussi" : "Échoué"} ({result.duration_ms}ms)
                </span>
              </div>
              {result.output && (
                <pre className="text-xs font-mono text-text bg-surface p-2 rounded mt-2 overflow-x-auto">
                  {result.output}
                </pre>
              )}
              {result.error && (
                <pre className="text-xs font-mono text-red-400 bg-surface p-2 rounded mt-2 overflow-x-auto">
                  {result.error}
                </pre>
              )}
            </div>
          )}
        </div>

        {/* History */}
        <div className="space-y-4">
          <button
            onClick={loadResults}
            className="text-sm text-ethan-400 hover:text-ethan-300 transition-colors"
          >
            Voir l'historique des tests →
          </button>

          {showResults && (
            <div className="space-y-2">
              {results.length === 0 && (
                <p className="text-text-dim text-sm">Aucun test enregistré</p>
              )}
              {results.map((r) => (
                <div
                  key={r.id}
                  className="rounded-lg border border-border bg-surface-2 p-3"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-text">{r.skill_name}</span>
                    <span className="text-xs text-text-dim">{r.duration_ms}ms</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {r.passed ? (
                      <span className="text-xs text-green-400">✅ Réussi</span>
                    ) : (
                      <span className="text-xs text-red-400">❌ Échoué</span>
                    )}
                    <span className="text-xs text-text-dim">{r.status}</span>
                  </div>
                  {r.error && (
                    <pre className="text-xs font-mono text-red-400 mt-1 overflow-x-auto">
                      {r.error.slice(0, 200)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}