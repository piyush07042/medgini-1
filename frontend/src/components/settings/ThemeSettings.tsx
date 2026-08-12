import { useEffect, useState } from "react";
import Card from "../Card";
import toast from "react-hot-toast";

const STORAGE_KEY = "medigenie_theme";

type ThemeOption = "light" | "dark" | "system";

const options: Array<{ label: string; value: ThemeOption }> = [
  { label: "Light", value: "light" },
  { label: "Dark", value: "dark" },
  { label: "System", value: "system" },
];

function applyTheme(theme: ThemeOption) {
  const root = document.documentElement;

  if (theme === "dark") {
    root.classList.add("dark");
  } else if (theme === "light") {
    root.classList.remove("dark");
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.classList.toggle("dark", prefersDark);
  }
}

export default function ThemeSettings() {
  const [theme, setTheme] = useState<ThemeOption>("system");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeOption | null;
    if (stored) {
      setTheme(stored);
      applyTheme(stored);
    } else {
      applyTheme("system");
    }
  }, []);

  const handleChange = (value: ThemeOption) => {
    setTheme(value);
    localStorage.setItem(STORAGE_KEY, value);
    applyTheme(value);
    const label = options.find((o) => o.value === value)?.label || value;
    toast.success(`Theme set to ${label}`);
  };

  return (
    <Card title="Theme preferences">
      <p className="text-sm text-slate-500">Choose your preferred application theme. This setting is stored locally in your browser.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => handleChange(option.value)}
            className={`rounded-3xl border px-4 py-3 text-sm font-semibold transition ${
              theme === option.value
                ? "border-brand-500 bg-brand-50 text-brand-700"
                : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </Card>
  );
}
