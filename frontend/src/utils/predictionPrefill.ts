import type { PredictionField } from "../components/predictions/PredictionPageShell";

const fieldNameMatch = (fieldName: string, metricKey: string) => fieldName.toLowerCase() === metricKey.toLowerCase();

export function buildPredictionFormValues<TValues extends Record<string, any>>(
  defaultValues: TValues,
  extractedMetrics?: Record<string, any> | null,
  patientContext?: Record<string, any> | null,
): TValues {
  const values: Record<string, any> = { ...defaultValues };

  if (patientContext) {
    for (const key of Object.keys(values)) {
      if (typeof patientContext[key] !== "undefined") {
        values[key] = patientContext[key];
      }
    }
  }

  if (extractedMetrics) {
    for (const [key, value] of Object.entries(extractedMetrics)) {
      const existing = Object.keys(values).find((field) => fieldNameMatch(field, key));
      if (existing && value !== undefined && value !== null) {
        values[existing] = value;
      }
    }
  }

  return values as TValues;
}
