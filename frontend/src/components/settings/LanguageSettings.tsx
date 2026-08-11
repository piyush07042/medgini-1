import { useEffect, useState } from "react";
import Card from "../Card";

const STORAGE_KEY = "medigenie_language";

const languages = [
  { label: "English", value: "en" },
  { label: "Hindi", value: "hi" },
];

export default function LanguageSettings() {
  const [language, setLanguage] = useState<string>("en");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setLanguage(stored);
    }
  }, []);

  const handleChange = (value: string) => {
    setLanguage(value);
    localStorage.setItem(STORAGE_KEY, value);
  };

  return (
    <Card title="Language preferences">
      <p className="text-sm text-slate-500">Select the display language for the MediGenie UI. This preference is stored locally.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {languages.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => handleChange(option.value)}
            className={`rounded-3xl border px-4 py-3 text-sm font-semibold transition ${
              language === option.value
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
