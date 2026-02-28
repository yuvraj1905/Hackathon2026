"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

interface ThemeToggleProps {
  inline?: boolean;
  className?: string;
}

export function ThemeToggle({ inline = false, className = "" }: ThemeToggleProps) {
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  // Load initial theme from localStorage or default
  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = (localStorage.getItem("na-theme") as "light" | "dark" | null) ?? "dark";
    setTheme(stored);
  }, []);

  // Apply theme to <html> and persist
  useEffect(() => {
    if (typeof window === "undefined") return;
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("na-theme", theme);
  }, [theme]);

  const base =
    "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border/70 bg-background/90 text-muted-foreground shadow-sm backdrop-blur-md transition hover:text-foreground hover:shadow-lg";
  const position = inline ? "" : "fixed right-4 top-4 z-50";

  return (
    <button
      type="button"
      onClick={() => setTheme((prev) => (prev === "dark" ? "light" : "dark"))}
      className={`${base} ${position} ${className}`.trim()}
      aria-label="Toggle theme"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

