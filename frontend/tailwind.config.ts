import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        soft: {
          bg: "#F0F4F8",
          shadow: "#D1D9E6",
          light: "#FFFFFF",
          blue: {
            DEFAULT: "#2563EB",
            hover: "#1D4ED8",
            active: "#1E40AF",
            subtle: "#EFF6FF",
          },
          green: {
            DEFAULT: "#22C55E",
            text: "#15803D",
            subtle: "#F0FDF4",
          },
          orange: {
            DEFAULT: "#EA580C",
            text: "#C2410C",
            subtle: "#FFF7ED",
          },
          text: {
            DEFAULT: "#1F2937",
            muted: "#4B5563",
            subtle: "#9CA3AF",
          },
          border: "#E2E8F0",
        },
      },
      boxShadow: {
        "soft-surface": "-6px -6px 15px #FFFFFF, 6px 6px 15px #D1D9E6",
        "soft-surface-sm": "-3px -3px 8px #FFFFFF, 3px 3px 8px #D1D9E6",
        "soft-surface-lg": "-10px -10px 25px #FFFFFF, 10px 10px 25px #D1D9E6",
        "soft-well": "inset -4px -4px 10px #FFFFFF, inset 4px 4px 10px #D1D9E6",
        "soft-well-sm": "inset -2px -2px 6px #FFFFFF, inset 2px 2px 6px #D1D9E6",
        "soft-button": "-4px -4px 10px #FFFFFF, 4px 4px 10px #D1D9E6",
        "soft-button-hover": "-2px -2px 6px #FFFFFF, 2px 2px 6px #D1D9E6",
        "soft-button-pressed": "inset -3px -3px 8px #FFFFFF, inset 3px 3px 8px #D1D9E6",
      },
      borderRadius: {
        "soft-sm": "0.5rem",
        "soft-md": "0.75rem",
        "soft-lg": "1.0rem",
        "soft-xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
