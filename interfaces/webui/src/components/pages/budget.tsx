"use client";

import { useEffect, useState } from "react";
import { api, type BudgetEntry } from "@/lib/api";
import { formatTime } from "@/lib/utils";
import { motion } from "framer-motion";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis } from "recharts";
import { Receipt } from "lucide-react";

const COLORS = ["#60a5fa", "#22c55e", "#eab308", "#ef4444", "#a855f7", "#06b6d4"];

export function BudgetPage() {
  const [entries, setEntries] = useState<BudgetEntry[]>([]);
  const [summary, setSummary] = useState<{ total: number; by_category: Record<string, number> } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [entries, summary] = await Promise.all([
          api.getBudget(100),
          api.getBudgetSummary(),
        ]);
        setEntries(entries);
        setSummary(summary);
      } catch {}
      setLoading(false);
    };
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const pieData = summary
    ? Object.entries(summary.by_category).map(([name, value]) => ({ name, value }))
    : [];

  if (loading && entries.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-text">Budget</h1>
        <div className="animate-pulse text-text-dim text-center py-8">Chargement...</div>
      </div>
    );
  }

  return (
    <motion.div className="space-y-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      <div>
        <h1 className="text-2xl font-bold text-text">Budget</h1>
        <p className="text-text-dim text-sm mt-1">Suivi des coûts</p>
      </div>

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
            <div className="text-2xl font-bold text-green-400">{summary.total.toFixed(2)}</div>
            <div className="text-xs text-green-400/80 mt-1">Total</div>
          </div>
          {Object.entries(summary.by_category).slice(0, 3).map(([cat, amount]) => (
            <div key={cat} className="rounded-lg border border-border bg-surface-2 p-4">
              <div className="text-xl font-bold text-text">{amount.toFixed(2)}</div>
              <div className="text-xs text-text-dim mt-1 capitalize">{cat}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <motion.div className="rounded-lg border border-border bg-surface-2 p-4" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <h3 className="text-sm font-medium text-text-dim mb-4">Répartition</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
                {pieData.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "12px" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div className="rounded-lg border border-border bg-surface-2 p-4" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }}>
          <h3 className="text-sm font-medium text-text-dim mb-4">Par catégorie</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={pieData}>
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", fontSize: "12px" }} />
              <Bar dataKey="value" fill="#60a5fa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium text-text-dim">Dernières entrées</h3>
        {entries.map((entry) => (
          <div key={entry.id} className="flex items-center justify-between rounded-lg border border-border bg-surface-2 p-3">
            <div className="flex items-center gap-3">
              <Receipt size={14} className="text-ethan-400 shrink-0" />
              <div>
                <p className="text-sm text-text">{entry.description}</p>
                <p className="text-xs text-text-dim capitalize">{entry.category}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-warning">{entry.amount.toFixed(4)}</p>
              <p className="text-xs text-text-dim">{formatTime(entry.timestamp)}</p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}