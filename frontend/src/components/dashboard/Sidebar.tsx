import { useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Cpu,
  Users,
  Upload,
  ShieldCheck,
  ClipboardPaste,
  MessageSquare,
  BookOpen as ClinicalBookOpen,
  Settings,
  Activity,
  X,
  BrainCircuit,
  Brain,
} from "lucide-react";


const navItems = [
  { label: "Dashboard", path: "/", icon: Cpu },
  { label: "Patients", path: "/patients", icon: Users },
  { label: "Upload Medical Report", path: "/upload-report", icon: Upload },
  { label: "Disease Prediction", path: "/predictions", icon: ShieldCheck },
  { label: "AI Reports", path: "/reports", icon: ClipboardPaste },
  { label: "Drug Safety", path: "/drug-safety", icon: ClinicalBookOpen },

  { label: "AI Chat", path: "/chat", icon: MessageSquare },
  { label: "Clinical Guidelines", path: "/guidelines", icon: ClinicalBookOpen },
  { label: "Model Evaluation", path: "/model-evaluation", icon: Activity },
  { label: "Explainable AI", path: "/xai", icon: BrainCircuit },
  { label: "AI Workflow", path: "/workflow", icon: Brain },
  { label: "Settings", path: "/settings", icon: Settings },
];


export default function Sidebar({ isOpen = false, onClose }: { isOpen?: boolean; onClose?: () => void }) {
  const location = useLocation();

  // Close sidebar on route change on mobile
  useEffect(() => {
    if (isOpen && onClose) {
      onClose();
    }
  }, [location.pathname]);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm transition-opacity xl:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex h-full w-80 flex-col gap-6 border-r border-slate-200 bg-white px-6 py-8 shadow-2xl transition-transform duration-300 xl:static xl:translate-x-0 xl:rounded-3xl xl:border xl:shadow-soft ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Navigation</p>
            <h2 className="text-2xl font-semibold text-slate-900">MediGenie Suite</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close navigation sidebar"
            className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-600 xl:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                  isActive ? "bg-brand-500 text-white" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-brand-600">
                <Icon className="h-5 w-5" />
              </span>
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      </aside>
    </>
  );
}
