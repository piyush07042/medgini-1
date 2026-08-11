import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import PageHeading from "../components/PageHeading";
import Card from "../components/Card";
import { listPatients } from "../api/patients";
import { getReportHtmlUrl, getReportPdfDownloadUrl, listReportTemplates } from "../api/reports";
import type { ReportTemplateResponse } from "../types/api";
import { clearReportHistory, loadReportHistory, saveReportHistoryEntry } from "../utils/reportHistory";
import type { Patient } from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export default function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryPatientIdString = searchParams.get("patientId");
  const queryPatientId = queryPatientIdString ? Number(queryPatientIdString) : NaN;
  const initialPatientId = Number.isInteger(queryPatientId) && queryPatientId > 0 ? queryPatientId : null;
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(initialPatientId);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("report_template.html");
  const [reportMode, setReportMode] = useState<"html" | "pdf">("html");
  const [filter, setFilter] = useState("");
  const [history, setHistory] = useState(loadReportHistory());
  const [versionNote, setVersionNote] = useState("Clinical summary update");

  const patientsQuery = useQuery({ queryKey: ["patients"], queryFn: () => listPatients(), staleTime: 1000 * 60 * 5 });
  const templatesQuery = useQuery<ReportTemplateResponse>({ queryKey: ["reportTemplates"], queryFn: listReportTemplates, staleTime: 1000 * 60 * 10 });

  const patients: Patient[] = patientsQuery.data?.data ?? [];
  const selectedPatient = useMemo(
    () => patients.find((patient: Patient) => String(patient.id) === String(selectedPatientId)) ?? null,
    [patients, selectedPatientId]
  );

  useEffect(() => {
    if (initialPatientId && initialPatientId !== selectedPatientId) {
      setSelectedPatientId(initialPatientId);
    } else if (!selectedPatientId && patients.length > 0) {
      setSelectedPatientId(patients[0].id);
    }
  }, [initialPatientId, selectedPatientId, patients]);

  useEffect(() => {
    if (templatesQuery.data?.templates?.length) {
      setSelectedTemplate(templatesQuery.data.templates[0]);
    }
  }, [templatesQuery.data]);

  const filteredPatients = useMemo(() => {
    if (!filter.trim()) return patients;
    const text = filter.toLowerCase();
    return patients.filter((patient: Patient) => {
      const fullName = `${patient.first_name} ${patient.last_name}`.toLowerCase();
      return (
        fullName.includes(text) ||
        String(patient.id).includes(text) ||
        patient.gender.toLowerCase().includes(text)
      );
    });
  }, [filter, patients]);

  const reportUrl = useMemo(() => {
    if (!selectedPatientId) return null;
    if (reportMode === "pdf") {
      return `${API_BASE_URL}${getReportPdfDownloadUrl(selectedPatientId)}`;
    }
    return `${API_BASE_URL}${getReportHtmlUrl(selectedPatientId, selectedTemplate)}`;
  }, [reportMode, selectedPatientId, selectedTemplate]);

  const handlePatientSelect = (patientId: number) => {
    setSelectedPatientId(patientId);
    setSearchParams({ patientId: String(patientId) });
  };

  const handleShare = async () => {
    if (!selectedPatient) {
      return;
    }

    const nextHistory = saveReportHistoryEntry({
      patientId: selectedPatient.id,
      patientName: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
      template: selectedTemplate,
      mode: reportMode,
      url: reportUrl ?? "",
      viewedAt: new Date().toISOString(),
      summary: `${selectedPatient.first_name} ${selectedPatient.last_name} • ${reportMode.toUpperCase()} report`,
    });
    setHistory(nextHistory);
    navigator.clipboard.writeText(reportUrl ?? "").catch(() => undefined);
  };

  const handleVersionSave = () => {
    if (!selectedPatient) {
      return;
    }

    const nextHistory = saveReportHistoryEntry({
      patientId: selectedPatient.id,
      patientName: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
      template: selectedTemplate,
      mode: reportMode,
      url: reportUrl ?? "",
      viewedAt: new Date().toISOString(),
      summary: `${versionNote || "Version update"} · ${selectedPatient.first_name} ${selectedPatient.last_name}`,
    });
    setHistory(nextHistory);
  };

  return (
    <div className="space-y-10">
      <PageHeading title="AI Report Center" description="Search patients and preview generated clinical reports with a single click." />

      {/* Top Controls Grid */}
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Card title="Patient reports">
          <div className="space-y-5">
            <div>
              <label htmlFor="patient-search" className="block text-sm font-medium text-slate-700">
                Search patients
              </label>
              <input
                id="patient-search"
                type="search"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                placeholder="Search by name, ID, or gender"
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
              />
            </div>

            {patientsQuery.isLoading ? (
              <div className="space-y-3 py-4">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="h-16 rounded-3xl bg-slate-100" />
                ))}
              </div>
            ) : patients.length === 0 ? (
              <p className="text-sm text-slate-500">No patients found. Add a patient or upload a report to see available reports.</p>
            ) : (
              <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {filteredPatients.slice(0, 20).map((patient: Patient) => (
                  <button
                    key={patient.id}
                    type="button"
                    onClick={() => handlePatientSelect(patient.id)}
                    className={`w-full rounded-3xl border px-4 py-4 text-left transition ${
                      String(selectedPatientId) === String(patient.id)
                        ? "border-brand-500 bg-brand-50 shadow-sm"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    <p className="font-semibold text-slate-900">{patient.first_name} {patient.last_name}</p>
                    <p className="mt-1 text-sm text-slate-500">ID {patient.id} · Age {patient.age} · {patient.gender}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card title="Report Configuration & Controls">
          <div className="space-y-5">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Selected patient</p>
              {selectedPatient ? (
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-800">
                  <div>
                    <p className="font-bold text-slate-900 text-base">{selectedPatient.first_name} {selectedPatient.last_name}</p>
                    <p className="text-slate-500">ID #{selectedPatient.id} · Age {selectedPatient.age} · {selectedPatient.gender}</p>
                  </div>
                  <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
                    Active
                  </span>
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-500">Choose a patient from the left panel to preview a report.</p>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Preview Mode</p>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => setReportMode("html")}
                    className={`rounded-2xl px-5 py-3 text-sm font-semibold transition ${
                      reportMode === "html" ? "bg-brand-600 text-white shadow-soft" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    HTML Interactive Preview
                  </button>
                  <button
                    type="button"
                    onClick={() => setReportMode("pdf")}
                    className={`rounded-2xl px-5 py-3 text-sm font-semibold transition ${
                      reportMode === "pdf" ? "bg-brand-600 text-white shadow-soft" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    PDF Document Preview
                  </button>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="template" className="block text-sm font-medium text-slate-700">
                    Report Template
                  </label>
                  <select
                    id="template"
                    value={selectedTemplate}
                    onChange={(event) => setSelectedTemplate(event.target.value)}
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                    disabled={templatesQuery.isLoading || !templatesQuery.data?.templates?.length}
                  >
                    {templatesQuery.data?.templates?.map((template) => (
                      <option key={template} value={template}>
                        {template}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <p className="text-sm font-medium text-slate-700 mb-2">Export & Share</p>
                  <div className="flex gap-2">
                    <a
                      href={selectedPatientId ? `${API_BASE_URL}${getReportPdfDownloadUrl(selectedPatientId)}` : "#"}
                      target="_blank"
                      rel="noreferrer"
                      className={`flex-1 inline-flex items-center justify-center rounded-2xl px-4 py-3 text-sm font-semibold text-white transition ${
                        selectedPatientId ? "bg-brand-600 hover:bg-brand-700 shadow-soft" : "bg-slate-300 text-slate-500 cursor-not-allowed"
                      }`}
                      aria-disabled={!selectedPatientId}
                    >
                      Download PDF
                    </a>
                    <button
                      type="button"
                      onClick={handleShare}
                      className="flex-1 inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                    >
                      Share Link
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Bottom Full-Width Report Preview Box */}
      <Card title="Clinical Report Viewer">
        <div className="rounded-3xl border border-slate-200 bg-slate-950 p-4">
          {reportUrl ? (
            <iframe
              src={reportUrl}
              title="Report viewer"
              className="h-[750px] w-full rounded-2xl border border-slate-800 bg-white shadow-2xl"
            />
          ) : (
            <div className="flex h-[450px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-6 text-center">
              <p className="mb-3 text-xl font-bold text-white">Pick a patient to preview the report</p>
              <p className="max-w-[32rem] text-sm text-slate-400 leading-relaxed">
                Select any patient from the list above to render their complete, AI-synthesized clinical report in real-time.
              </p>
            </div>
          )}
        </div>
      </Card>

          <Card title="Recent report history">
            {history.length ? (
              <div className="space-y-3">
                {history.map((item) => (
                  <div key={item.id} className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">{item.patientName}</p>
                        <p className="mt-1 text-sm text-slate-500">{item.mode.toUpperCase()} • {item.template}</p>
                      </div>
                      <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">
                        v{item.version}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{item.summary}</p>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setHistory(clearReportHistory())}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Clear history
                </button>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No report history yet. Preview a report to add it here.</p>
            )}
          </Card>
    </div>
  );
}
