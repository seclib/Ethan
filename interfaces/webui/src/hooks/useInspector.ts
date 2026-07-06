"use client";

import { useEffect, useState } from "react";

export function useInspector() {
  const [active, setActive] = useState(false);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Alt") {
        setActive(true);
        document.body.classList.add("inspector-active");
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.key === "Alt") {
        setActive(false);
        document.body.classList.remove("inspector-active");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      document.body.classList.remove("inspector-active");
    };
  }, []);

  return active;
}