/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Odysseus core palette — RGB triplets → support natif des
        // modificateurs d'opacité (bg-accent/10, text-fg/70, …)
        background: "rgb(var(--bg-rgb) / <alpha-value>)",
        bg: {
          0: "rgb(var(--bg-rgb) / <alpha-value>)",
          1: "rgb(var(--panel-rgb) / <alpha-value>)",
          "1.5": "var(--surface-secondary)",
          2: "rgb(var(--muted-rgb) / <alpha-value>)",
          3: "rgb(var(--surface-elevated-rgb) / <alpha-value>)",
        },
        surface: {
          DEFAULT: "rgb(var(--panel-rgb) / <alpha-value>)",
          secondary: "var(--surface-secondary)",
          elevated: "rgb(var(--surface-elevated-rgb) / <alpha-value>)",
          hover: "rgb(var(--panel-rgb) / <alpha-value>)",
        },
        elevated: "rgb(var(--surface-elevated-rgb) / <alpha-value>)",

        foreground: {
          DEFAULT: "rgb(var(--fg-rgb) / <alpha-value>)",
          secondary: "rgb(var(--fg-rgb) / 0.7)",
          tertiary: "rgb(var(--fg-rgb) / calc(<alpha-value> * 0.5))",
        },

        accent: {
          DEFAULT: "rgb(var(--accent-rgb) / <alpha-value>)",
          soft: "var(--accent-soft)",
          line: "var(--accent-line)",
          400: "color-mix(in srgb, var(--accent) 80%, white)",
          500: "rgb(var(--accent-rgb) / <alpha-value>)",
          600: "rgb(var(--accent-rgb) / <alpha-value>)",
        },

        error: {
          DEFAULT: "rgb(var(--red-rgb) / <alpha-value>)",
          soft: "var(--red-soft)",
          400: "color-mix(in srgb, var(--red) 78%, white)",
          500: "rgb(var(--red-rgb) / <alpha-value>)",
          600: "rgb(var(--red-rgb) / <alpha-value>)",
        },
        success: {
          DEFAULT: "rgb(var(--green-rgb) / <alpha-value>)",
          soft: "var(--green-soft)",
          500: "rgb(var(--green-rgb) / <alpha-value>)",
        },
        warning: {
          DEFAULT: "rgb(var(--amber-rgb) / <alpha-value>)",
          soft: "var(--amber-soft)",
          500: "rgb(var(--amber-rgb) / <alpha-value>)",
        },
        destructive: {
          DEFAULT: "rgb(var(--red-rgb) / <alpha-value>)",
          foreground: "var(--bg)",
        },

        border: {
          DEFAULT: "rgb(var(--border-rgb) / <alpha-value>)",
        },
        line: {
          1: "rgb(var(--line-1-rgb) / <alpha-value>)",
          2: "rgb(var(--line-2-rgb) / <alpha-value>)",
          3: "rgb(var(--line-3-rgb) / <alpha-value>)",
        },

        gold: { DEFAULT: "rgb(var(--gold-rgb) / <alpha-value>)", soft: "var(--gold-soft)" },
        green: { DEFAULT: "rgb(var(--green-rgb) / <alpha-value>)", soft: "var(--green-soft)", 500: "rgb(var(--green-rgb) / <alpha-value>)" },
        red: { DEFAULT: "rgb(var(--red-rgb) / <alpha-value>)", soft: "var(--red-soft)", 500: "rgb(var(--red-rgb) / <alpha-value>)" },
        amber: { DEFAULT: "rgb(var(--amber-rgb) / <alpha-value>)", soft: "var(--amber-soft)", 500: "rgb(var(--amber-rgb) / <alpha-value>)" },
        purple: { DEFAULT: "rgb(var(--purple-rgb) / <alpha-value>)", soft: "var(--purple-soft)", 500: "rgb(var(--purple-rgb) / <alpha-value>)" },

        muted: {
          DEFAULT: "rgb(var(--muted-rgb) / <alpha-value>)",
          foreground: "rgb(var(--fg-rgb) / calc(<alpha-value> * 0.55))",
        },

        card: {
          DEFAULT: "var(--panel)",
          foreground: "var(--fg)",
        },

        secondary: {
          DEFAULT: "rgb(var(--muted-rgb) / <alpha-value>)",
          foreground: "var(--fg)",
        },
      },
      fontFamily: {
        mono: ["Fira Code", "JetBrains Mono", "monospace"],
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
