import { TerminalClient } from "@/components/features/terminal/terminal-client";

export const metadata = { title: "Terminal - ETHAN" };

export default function TerminalPage() {
  return (
    <div className="mx-auto h-full w-full max-w-6xl px-4 py-6">
      <TerminalClient />
    </div>
  );
}