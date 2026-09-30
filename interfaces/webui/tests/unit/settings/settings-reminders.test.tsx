/**
 * Tests — Settings → Reminders : rappels réellement planifiés par le Core.
 *
 * Contrat (audit anti-fantôme 2026-09-30) : la section Reminders lit/écrit
 * `/reminders` (ReminderManager Core). Les préférences inventées (Default
 * Timezone, Notification Sound, Auto-dismiss) ont été supprimées : rien de
 * simulé, la planification reste 100 % Core.
 */
import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockList = jest.fn();
const mockCreate = jest.fn();
const mockDelete = jest.fn();
const mockEnable = jest.fn();
const mockDisable = jest.fn();

jest.mock("@/lib/api/reminders", () => ({
  listReminders: (...args: unknown[]) => mockList(...args),
  createReminder: (...args: unknown[]) => mockCreate(...args),
  deleteReminder: (...args: unknown[]) => mockDelete(...args),
  enableReminder: (...args: unknown[]) => mockEnable(...args),
  disableReminder: (...args: unknown[]) => mockDisable(...args),
}));

import { RemindersSection } from "../../../src/components/features/settings/components/settings-sections";
import type { Reminder } from "@/lib/api/reminders";

function makeReminder(over: Partial<Reminder> = {}): Reminder {
  return {
    id: "r-1",
    title: "Veille quotidienne",
    message: "",
    schedule: "0 9 * * *",
    fire_at: null,
    timezone: "UTC",
    enabled: true,
    last_fired_at: null,
    fire_count: 0,
    metadata: {},
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
    ...over,
  };
}

function renderSection() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <RemindersSection />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  for (const fn of [mockList, mockCreate, mockDelete, mockEnable, mockDisable]) fn.mockReset();
});

describe("Settings → Reminders", () => {
  it("état vide explicite quand le Core n'a aucun rappel", async () => {
    mockList.mockResolvedValue([]);
    renderSection();

    expect(await screen.findByText("Aucun rappel dans ETHAN Core.")).toBeInTheDocument();
  });

  it("affiche les rappels réels (cron, état actif/inactif)", async () => {
    mockList.mockResolvedValue([
      makeReminder(),
      makeReminder({ id: "r-2", title: "One-shot", schedule: null, fire_at: "2026-10-01T09:00:00Z", enabled: false }),
    ]);
    renderSection();

    expect(await screen.findByText("Veille quotidienne")).toBeInTheDocument();
    expect(screen.getByText(/Cron 0 9 \* \* \*/)).toBeInTheDocument();
    expect(screen.getByText("actif")).toBeInTheDocument();
    expect(screen.getByText("inactif")).toBeInTheDocument();
  });

  it("désactiver un rappel appelle réellement le Core (disable)", async () => {
    mockList.mockResolvedValue([makeReminder()]);
    mockDisable.mockResolvedValue(makeReminder({ enabled: false }));
    renderSection();

    fireEvent.click(await screen.findByRole("button", { name: "Désactiver Veille quotidienne" }));

    await waitFor(() => expect(mockDisable).toHaveBeenCalledWith("r-1"));
  });

  it("supprimer un rappel exige confirmation puis appelle le Core (delete)", async () => {
    mockList.mockResolvedValue([makeReminder()]);
    mockDelete.mockResolvedValue({ status: "deleted", reminder_id: "r-1" });
    renderSection();

    fireEvent.click(await screen.findByRole("button", { name: "Supprimer Veille quotidienne" }));
    expect(screen.getByText("Supprimer ce rappel ?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Supprimer" }));

    await waitFor(() => expect(mockDelete).toHaveBeenCalledWith("r-1"));
  });

  it("créer un rappel : validation locale puis POST Core avec fuseau navigateur", async () => {
    mockList.mockResolvedValue([]);
    mockCreate.mockResolvedValue(makeReminder());
    renderSection();

    fireEvent.click(await screen.findByRole("button", { name: /Nouveau rappel/ }));
    fireEvent.click(screen.getByRole("button", { name: "Créer" }));
    expect(screen.getByText("Un titre est requis.")).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Titre"), { target: { value: "Veille" } });
    fireEvent.change(screen.getByLabelText("Date et heure"), {
      target: { value: "2026-10-01T09:00" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Créer" }));

    await waitFor(() => expect(mockCreate).toHaveBeenCalledTimes(1));
    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Veille", timezone: expect.any(String), fire_at: expect.any(String) }),
    );
  });

  it("Core injoignable : état d'erreur explicite (aucun remplacement simulé)", async () => {
    mockList.mockRejectedValue(new Error("core indisponible"));
    renderSection();

    expect(await screen.findByText(/Rappels indisponibles/)).toBeInTheDocument();
  });
});
