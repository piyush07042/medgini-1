import { useLocation, useNavigate } from "react-router-dom";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";

export default function ProcessingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as {
    status?: string;
    fileName?: string;
    progress?: number;
    startedAt?: string;
  } | null;

  return (
    <div className="space-y-10">
      <PageHeading title="Processing report" description="Your uploaded report is being processed by the AI workflow." />

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Upload status">
          {state?.fileName ? (
            <div className="space-y-4 text-sm text-slate-700">
              <p className="font-medium">File</p>
              <p>{state.fileName}</p>
              <p className="font-medium">Status</p>
              <p>{state.status ?? "Processing"}</p>
              <p className="font-medium">Progress</p>
              <p>{state.progress ? `${state.progress}%` : "Starting..."}</p>
              {state.startedAt ? <p>Started at {new Date(state.startedAt).toLocaleString()}</p> : null}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No active upload was found. Start from the Upload Report page.</p>
          )}

          <button
            type="button"
            onClick={() => navigate("/upload-report")}
            className="mt-6 w-full rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            Back to upload
          </button>
        </Card>

        <Card title="Processing details">
          <p className="text-sm text-slate-500">
            This page displays live upload progress when the workflow is triggered from the upload page. If you happen to land here directly, use the upload page to start a new report.
          </p>
        </Card>
      </div>
    </div>
  );
}
