"use client";

/**
 * Page Channels — canaux de discussion persistés par ETHAN Core
 * (ChannelStore, core/state/channels.py ; /v1/channels).
 *
 * L'interface affiche les canaux et leurs messages et envoie les nouveaux
 * messages au Core, qui les persiste et publie `channel.message` sur le bus.
 */

import { ChannelsWorkspace } from "@/components/features/channels/channels-workspace";

export default function ChannelsPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ChannelsWorkspace />
    </div>
  );
}
