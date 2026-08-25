"use client";

/**
 * Page Calendrier — vue mois + gestion d'événements.
 * Toute la logique vit dans ETHAN Core (CalendarManager) ; cette page
 * ne fait que rendre les données et envoyer les actions via l'API.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCalendarEvents, createCalendarEvent, deleteCalendarEvent } from "@/lib/api/capabilities";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { CalendarDays, Plus, Trash2, ChevronLeft, ChevronRight } from "lucide-react";

const MONTHS = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];
const DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

function fmtDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function CalendarPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [cursor, setCursor] = React.useState(() => new Date());
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [title, setTitle] = React.useState("");
  const [date, setDate] = React.useState(fmtDate(new Date()));
  const [time, setTime] = React.useState("09:00");

  const { data: events = [], isLoading } = useQuery({
    queryKey: ["calendar"],
    queryFn: () => listCalendarEvents(),
  });

  const createMutation = useMutation({
    mutationFn: createCalendarEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
      addToast({ type: "success", message: "Événement créé" });
      setDialogOpen(false);
      setTitle("");
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCalendarEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
      addToast({ type: "success", message: "Événement supprimé" });
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const year = cursor.getFullYear();
  const month = cursor.getMonth();
  const first = new Date(year, month, 1);
  const startOffset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (Date | null)[] = [
    ...Array.from({ length: startOffset }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => new Date(year, month, i + 1)),
  ];
  while (cells.length % 7 !== 0) cells.push(null);

  const eventsByDay = React.useMemo(() => {
    const map: Record<string, typeof events> = {};
    for (const ev of events) {
      const key = String(ev.start_time).slice(0, 10);
      (map[key] ||= []).push(ev);
    }
    return map;
  }, [events]);

  const todayStr = fmtDate(new Date());

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b border-line-1 px-4 py-3" style={{ background: "var(--panel)", borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2">
          <CalendarDays size={18} className="text-accent" />
          <h1 className="text-base font-semibold">Calendrier</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => setCursor(new Date(year, month - 1, 1))} aria-label="Mois précédent"><ChevronLeft size={16} /></Button>
          <span className="min-w-[140px] text-center text-sm font-medium">{MONTHS[month]} {year}</span>
          <Button variant="ghost" size="icon" onClick={() => setCursor(new Date(year, month + 1, 1))} aria-label="Mois suivant"><ChevronRight size={16} /></Button>
          <Button size="sm" onClick={() => { setDate(fmtDate(cursor)); setDialogOpen(true); }}><Plus size={14} /> Événement</Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-7 gap-px overflow-hidden rounded-lg" style={{ background: "var(--border)", border: "1px solid var(--border)" }}>
          {DAYS.map((d) => (
            <div key={d} className="px-2 py-1.5 text-center text-xs font-semibold uppercase tracking-wide" style={{ background: "var(--panel)" }}>{d}</div>
          ))}
          {cells.map((cell, i) => {
            if (!cell) return <div key={`e${i}`} className="min-h-[90px]" style={{ background: "var(--panel)" }} />;
            const key = fmtDate(cell);
            const dayEvents = eventsByDay[key] || [];
            const isToday = key === todayStr;
            return (
              <div key={key} className="min-h-[90px] p-1.5" style={{ background: "var(--panel)" }}
                onDoubleClick={() => { setDate(key); setDialogOpen(true); }}>
                <div className={"mb-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-xs" + (isToday ? " font-bold text-white" : "")}
                  style={isToday ? { background: "var(--accent)" } : undefined}>
                  {cell.getDate()}
                </div>
                {dayEvents.slice(0, 3).map((ev) => (
                  <div key={ev.id} className="group flex items-center gap-1 truncate rounded px-1 py-0.5 text-[11px]"
                    style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
                    title={`${String(ev.start_time).slice(11, 16)} ${ev.title}`}>
                    <span className="flex-1 truncate">{ev.title}</span>
                    <button className="hidden group-hover:inline" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(ev.id); }} aria-label="Supprimer">
                      <Trash2 size={10} />
                    </button>
                  </div>
                ))}
                {dayEvents.length > 3 && <div className="px-1 text-[10px] opacity-50">+{dayEvents.length - 3}</div>}
              </div>
            );
          })}
        </div>
        {isLoading && <p className="mt-3 text-sm opacity-60">Chargement…</p>}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen} title="Nouvel événement">
        <form className="space-y-3" onSubmit={(e) => {
          e.preventDefault();
          if (!title.trim()) return;
          createMutation.mutate({ title: title.trim(), start_time: `${date}T${time}:00` });
        }}>
          <Input placeholder="Titre" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <div className="flex gap-2">
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <Input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
          <Button type="submit" className="w-full" disabled={!title.trim() || createMutation.isPending}>Créer</Button>
        </form>
      </Dialog>
    </div>
  );
}
