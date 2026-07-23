import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand
        ethan: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
          950: "#1e1b4b",
        },

        // Surface tokens (CSS custom properties)
        background: "hsl(var(--background))",
        surface: {
          DEFAULT: "hsl(var(--surface))",
          secondary: "hsl(var(--surface-secondary))",
          elevated: "hsl(var(--surface-elevated))",
        },
        elevated: "hsl(var(--elevated))",

        // Foreground tokens
        foreground: {
          DEFAULT: "hsl(var(--foreground))",
          secondary: "var(--fg-1)",
          tertiary: "var(--fg-3)",
        },

        // Semantic colors
        accent: {
          DEFAULT: "var(--accent)",
          soft: "var(--accent-soft)",
          line: "var(--accent-line)",
          "600": "var(--accent-600)",
          "500": "var(--accent-500, var(--accent))",
          "400": "var(--accent-400, var(--accent))",
          "/10": "var(--accent-soft)",
          "/20": "var(--accent-soft)",
          "/5": "var(--accent-soft)",
        },

        // Border tokens
        border: {
          DEFAULT: "hsl(var(--border))",
        },
        line: {
          "1": "var(--line-1)",
          "2": "var(--line-2)",
          "3": "var(--line-3)",
        },

        // Status colors
        gold: {
          DEFAULT: "var(--gold)",
          soft: "var(--gold-soft)",
        },
        green: {
          DEFAULT: "var(--green)",
          soft: "var(--green-soft)",
          "400": "var(--green)",
          "500": "var(--green)",
        },
        red: {
          DEFAULT: "var(--red)",
          soft: "var(--red-soft)",
        },
        amber: {
          DEFAULT: "var(--amber)",
          soft: "var(--amber-soft)",
        },
        purple: {
          DEFAULT: "var(--purple)",
          soft: "var(--purple-soft)",
        },

        // Muted (alias for accessibility)
        muted: {
          DEFAULT: "var(--bg-2)",
          foreground: "var(--fg-2)",
        },

        // Card
        card: {
          DEFAULT: "hsl(var(--surface))",
          foreground: "hsl(var(--foreground))",
        },

        // Secondary (for avatars, badges)
        secondary: {
          DEFAULT: "var(--bg-2)",
          foreground: "var(--fg-0)",
        },

        // Error
        error: {
          "600": "var(--red)",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      zIndex: {
        modal: "100",
      },
    },
  },
  plugins: [],
};

export default config;