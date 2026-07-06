"use client";

import { useState, useEffect } from "react";

interface Room {
  id: string;
  label: string;
  icon: string;
  href: string;
}

const ROOMS: Room[] = [
  { id: "home", label: "Home", icon: "⌂", href: "/" },
  { id: "dashboard", label: "Dashboard", icon: "◉", href: "/dashboard" },
  { id: "chat", label: "Chat", icon: "💬", href: "/chat" },
  { id: "settings", label: "Settings", icon: "⚙", href: "/settings" },
];

export function RoomsNavigation() {
  const [active, setActive] = useState(ROOMS[0].id);

  useEffect(() => {
    const path = window.location.pathname;
    const room = ROOMS.find((r) => path.startsWith(r.href));
    if (room) setActive(room.id);
  }, []);

  const navigate = (href: string) => {
    window.location.href = href;
  };

  return (
    <nav className="rooms-pages" data-active={active}>
      {ROOMS.map((room, i) => (
        <button
          key={room.id}
          data-active={active === room.id}
          onClick={() => navigate(room.href)}
        >
          <span className="num">{String(i + 1).padStart(2, "0")}</span>
          {room.icon} {room.label}
        </button>
      ))}
    </nav>
  );
}