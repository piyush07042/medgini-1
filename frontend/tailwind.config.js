/** @type {import('tailwindcss').Config} */
import forms from "@tailwindcss/forms";
import typography from "@tailwindcss/typography";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        soft: "0 15px 40px rgba(15, 23, 42, 0.08)",
      },
      colors: {
        brand: {
          50: "#f5f8ff",
          100: "#e9efff",
          200: "#cad7ff",
          300: "#a9bcff",
          400: "#7b95ff",
          500: "#4f6dff",
          600: "#3f57db",
          700: "#3246b0",
          800: "#273685",
          900: "#1d2b62",
        },
      },
    },
  },
  plugins: [forms, typography],
};
