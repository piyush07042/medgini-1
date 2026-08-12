import { useEffect, useState } from "react";
import Card from "../Card";
import toast from "react-hot-toast";

const STORAGE_KEY = "medigenie_notifications";

type NotificationOptions = {
  email: boolean;
  browser: boolean;
  predictionComplete: boolean;
  ocrComplete: boolean;
};

const defaultPreferences: NotificationOptions = {
  email: true,
  browser: true,
  predictionComplete: true,
  ocrComplete: true,
};

export default function NotificationSettings() {
  const [preferences, setPreferences] = useState<NotificationOptions>(defaultPreferences);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setPreferences(JSON.parse(stored));
      } catch {
        setPreferences(defaultPreferences);
      }
    }
  }, []);

  const updatePreference = (key: keyof NotificationOptions, value: boolean) => {
    const updated = { ...preferences, [key]: value };
    setPreferences(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    toast.success("Notification preference updated");
  };

  return (
    <Card title="Notification preferences">
      <p className="text-sm text-slate-500">Control your local notification settings. These options are stored in this browser only.</p>
      <div className="mt-6 space-y-4">
        {(
          Object.entries(preferences) as Array<[keyof NotificationOptions, boolean]>
        ).map(([key, value]) => (
          <label key={key} className="flex items-center justify-between rounded-3xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm font-medium text-slate-900">
            <span>
              {key === "email"
                ? "Email"
                : key === "browser"
                ? "Browser"
                : key === "predictionComplete"
                ? "Prediction Complete"
                : "OCR Complete"}
            </span>
            <input
              type="checkbox"
              checked={value}
              onChange={(event) => updatePreference(key, event.target.checked)}
              className="h-5 w-5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
          </label>
        ))}
      </div>
    </Card>
  );
}
