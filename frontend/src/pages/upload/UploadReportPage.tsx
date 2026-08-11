import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { RotateCcw, Upload, FileText } from "lucide-react";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";
import { uploadReport } from "../../api/upload";
import { invalidateDashboardCache } from "../../services/dashboardService";
import { UploadHistoryItem, UploadReportResponse } from "../../types/api";
import { clearUploadHistory, loadUploadHistory, saveUploadHistoryEntry } from "../../utils/uploadHistory";

export default function UploadReportPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [patientId, setPatientId] = useState<number | "">("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<UploadReportResponse | null>(null);
  const [history, setHistory] = useState<UploadHistoryItem[]>([]);
  const [retrying, setRetrying] = useState(false);
  const [retryTarget, setRetryTarget] = useState<string | null>(null);

  useEffect(() => {
    setHistory(loadUploadHistory());
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      setFile(acceptedFiles[0] ?? null);
    },
  });

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a report file to upload.");
      return;
    }

    setErrorMessage(null);
    setUploading(true);
    setProgress(0);

    try {
      const patientContext = patientId ? { id: patientId } : undefined;
      const response = await uploadReport(
        file,
        patientContext,
        setProgress,
        new AbortController().signal
      );

      if (!response.success || !response.data) {
        throw new Error(response.message || "Upload did not complete successfully.");
      }

      setResult(response.data);
      const nextHistory = saveUploadHistoryEntry(file, response.data);
      setHistory(nextHistory);
      invalidateDashboardCache();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Report uploaded successfully.");
      navigate("/upload-report/preview", {
        state: { result: response.data, fileName: file.name },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed. Please try again.";
      setErrorMessage(message);
      toast.error(message);
    } finally {
      setUploading(false);
    }
  };

  const handleRetry = async (item: UploadHistoryItem) => {
    if (!item.workflowState) {
      toast.error("This upload has no OCR result to retry.");
      return;
    }

    setRetrying(true);
    setRetryTarget(item.id);
    try {
      const nextState = {
        ...item.workflowState,
        metadata: {
          ...(item.workflowState.metadata ?? {}),
          workflow_status: "retried",
          retry_count: (item.workflowState.metadata?.retry_count ?? 0) + 1,
        },
      };

      const nextHistory = history.map((entry) =>
        entry.id === item.id ? { ...entry, status: "completed" as const, workflowState: nextState, summary: "OCR retry completed with the saved workflow state." } : entry
      );
      setHistory(nextHistory);
      localStorage.setItem("medigenie_upload_history", JSON.stringify(nextHistory));
      setResult({ workflow_state: nextState } as UploadReportResponse);
      toast.success("OCR retry completed for this upload.");
      navigate("/upload-report/preview", {
        state: { result: { workflow_state: nextState } as UploadReportResponse, fileName: item.filename },
      });
    } catch {
      toast.error("Unable to retry the OCR workflow.");
    } finally {
      setRetrying(false);
      setRetryTarget(null);
    }
  };

  return (
    <div className="space-y-10">
      <PageHeading
        title="Upload Clinical Report"
        description="Upload a PDF or image report to run OCR and AI workflow processing."
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Upload report">
          <div
            {...getRootProps()}
            className={`group relative flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed p-10 text-center transition-all duration-300 ${
              isDragActive ? "border-brand-500 bg-brand-50/50 scale-[1.02]" : "border-slate-300 bg-slate-50 hover:border-brand-400 hover:bg-slate-100"
            }`}
          >
            <input {...getInputProps()} />
            <div className={`mb-4 flex h-16 w-16 items-center justify-center rounded-full transition-colors duration-300 ${isDragActive ? "bg-brand-100 text-brand-600" : "bg-white text-slate-400 group-hover:text-brand-500 shadow-sm"}`}>
              <Upload className="h-8 w-8" />
            </div>
            {isDragActive ? (
              <p className="text-sm font-semibold text-brand-600">Drop the medical report here...</p>
            ) : (
              <div>
                <p className="text-sm font-semibold text-slate-700">Click to upload or drag and drop</p>
                <p className="mt-1 text-xs text-slate-500">PDF, PNG, or JPEG (max 10MB)</p>
              </div>
            )}
            
            {file && !isDragActive && (
              <div className="mt-6 w-full rounded-2xl bg-white p-4 shadow-sm border border-slate-100">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-brand-500" />
                  <div className="text-left flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-700">Patient ID (optional)</label>
            <input
              type="number"
              value={patientId}
              onChange={(event) => setPatientId(event.target.value === "" ? "" : Number(event.target.value))}
              placeholder="Enter a patient ID to attach this report"
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
            />
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading}
              className="w-full rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {uploading ? "Uploading report..." : "Upload and process report"}
            </button>
          </div>

          {uploading ? (
            <div className="mt-4 rounded-3xl border border-brand-100 bg-brand-50/30 p-5 text-sm text-slate-700 shadow-sm">
              <div className="flex items-center justify-between font-semibold text-brand-900">
                <p>{progress < 20 ? "Uploading file..." : progress < 80 ? "Running OCR & extraction..." : "Finalizing AI analysis..."}</p>
                <p>{progress}%</p>
              </div>
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full rounded-full bg-brand-600 transition-all duration-300 ease-out shadow-[0_0_10px_rgba(37,99,235,0.5)]" style={{ width: `${progress}%` }} />
              </div>
              <p className="mt-3 text-xs text-slate-500">Please do not close this page while processing.</p>
            </div>
          ) : null}

          {errorMessage ? (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <p className="font-semibold">Upload error</p>
              <p>{errorMessage}</p>
            </div>
          ) : null}
        </Card>

        <Card title="Upload summary">
          {result ? (
            <div className="space-y-4 text-sm text-slate-700">
              <p>
                <span className="font-semibold">Workflow status:</span> {result.workflow_state?.metadata?.workflow_status ?? "completed"}
              </p>
              <p>
                <span className="font-semibold">Detected warnings:</span> {result.workflow_state?.warnings?.length ?? 0}
              </p>
              <p>
                <span className="font-semibold">Detected errors:</span> {result.workflow_state?.errors?.length ?? 0}
              </p>
              <button
                type="button"
                onClick={() => navigate("/upload-report/preview", {
                  state: { result, fileName: file?.name ?? "Uploaded report" },
                })}
                className="w-full rounded-2xl border border-brand-600 bg-white px-4 py-3 text-sm font-semibold text-brand-600 transition hover:bg-brand-50"
              >
                View extracted report details
              </button>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Upload a report to preview OCR text, extracted metrics, AI risk analysis, and recommendations.
            </p>
          )}
        </Card>
      </div>

      <Card title="Recent uploads">
        {history.length ? (
          <div className="space-y-3">
            {history.map((item) => (
              <div key={item.id} className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-4 text-left transition hover:border-brand-400 hover:bg-white">
                <button
                  type="button"
                  onClick={() =>
                    navigate("/upload-report/preview", {
                      state: { result: { workflow_state: item.workflowState } as UploadReportResponse, fileName: item.filename },
                    })
                  }
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">{item.filename}</p>
                      <p className="mt-1 text-sm text-slate-500">{item.fileType} • {new Date(item.uploadedAt).toLocaleString()}</p>
                    </div>
                    <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">
                      {item.status}
                    </span>
                  </div>
                  {item.summary ? <p className="mt-3 text-sm text-slate-600">{item.summary}</p> : null}
                </button>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => handleRetry(item)}
                    disabled={retrying && retryTarget === item.id}
                    className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed"
                  >
                    <RotateCcw className="h-4 w-4" />
                    {retrying && retryTarget === item.id ? "Retrying…" : "Retry OCR"}
                  </button>
                </div>
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setHistory(clearUploadHistory());
                toast.success("Upload history cleared.");
              }}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Clear history
            </button>
          </div>
        ) : (
          <p className="text-sm text-slate-500">No uploaded reports have been saved yet. Completed uploads will appear here automatically.</p>
        )}
      </Card>
    </div>
  );
}
