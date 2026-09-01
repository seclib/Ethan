"use client";

/**
 * Page Gallery — catalogue visuel d'assistants/agents partagés.
 *
 * ETHAN Core ne possède pas encore de module gallery public (/v1/gallery absent).
 * Page créée pour respecter la taxonomie nav-config + politique UX : les items
 * sans backend exposent un état vide honnête, aucune donnée simulée.
 * Inspiré du pattern Open-WebUI *gallery* et Odysseus *hub*.
 */

import { GalleryVerticalEnd } from "lucide-react";

export default function GalleryPage() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-3 p-8 text-center">
      <GalleryVerticalEnd size={32} className="text-foreground-tertiary" />
      <h2 className="text-lg font-medium">Galerie — bientôt disponible</h2>
      <p className="max-w-md text-sm text-foreground-tertiary">
        La galerie d&apos;agents et assistants partagés sera activée lorsque
        le backend ETHAN exposera la route <code>/v1/gallery</code>.
      </p>
    </div>
  );
}
