import { useEffect, useMemo, useState, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { BookOpen, MessageSquareQuote, Sparkles } from "lucide-react";
import PageHeading from "../components/PageHeading";
import Card from "../components/Card";
import { listPatients } from "../api/patients";
import { sendChat, type ChatPayload, type ChatResponseData } from "../api/chat";
import { storeConversation, getConversationsForPatient } from "../api/chat";
import type { Patient } from "../types/api";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  sources?: string[];
  citedSources?: { name: string; excerpt: string }[];
  followUpSuggestions?: string[];
  clinicalIntelligence?: Record<string, unknown>;
  error?: boolean;
};

const CHAT_STORAGE_KEY = "medigenie_chat_history_v1";

const QUICK_PROMPTS = [
  "Summarize the patient's current risk profile and next steps.",
  "Review the latest clinical data and suggest a treatment plan.",
  "Identify any medication conflicts and allergy concerns.",
  "Explain this patient's potential diagnosis in plain terms.",
];

function formatTime(timestamp: string) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(timestamp));
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function extractSources(data: ChatResponseData | undefined) {
  const sources: string[] = [];
  const seen = new Set<string>();

  const addValues = (value: unknown) => {
    if (typeof value === "string" && value.trim()) {
      if (!seen.has(value)) {
        seen.add(value);
        sources.push(value);
      }
    }

    if (Array.isArray(value)) {
      value.forEach(addValues);
    }

    if (value && typeof value === "object") {
      const record = value as Record<string, unknown>;
      addValues(record.source);
      addValues(record.source_path);
      addValues(record.source_name);
      addValues(record.title);
      addValues(record.document);
      addValues(record.evidence);
      addValues(record.references);
      if (Array.isArray(record.sources)) {
        record.sources.forEach(addValues);
      }
    }
  };

  addValues(data?.workflow_state);
  addValues(data?.agent_results);
  addValues(data?.metrics);
  return sources.slice(0, 4);
}

export default function ChatPage() {
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [medications, setMedications] = useState("");
  const [allergies, setAllergies] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [clinicalSummary, setClinicalSummary] = useState<string | null>(null);
  const [followUpSuggestions, setFollowUpSuggestions] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const assistantBufferRef = useRef<string>("");
  const flushTimerRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const patientsQuery = useQuery({ queryKey: ["patients"], queryFn: () => listPatients(), staleTime: 1000 * 60 * 5 });
  const patients: Patient[] = patientsQuery.data?.data ?? [];

  const conversationsQuery = useQuery({
    queryKey: ["chatConversations", selectedPatientId],
    queryFn: () => (selectedPatientId ? getConversationsForPatient(selectedPatientId) : Promise.resolve({ success: true, message: "", data: [] })),
    enabled: Boolean(selectedPatientId),
    staleTime: 1000 * 30,
  });
  const savedConversations: any[] = conversationsQuery.data?.data ?? [];

  const selectedPatient = useMemo(
    () => patients.find((patient: Patient) => patient.id === selectedPatientId) ?? null,
    [patients, selectedPatientId]
  );

  useEffect(() => {
    const stored = localStorage.getItem(CHAT_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as ChatMessage[];
        setMessages(parsed);
      } catch {
        setMessages([]);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  const handleConversationReset = () => {
    setMessages([]);
    setClinicalSummary(null);
    localStorage.removeItem(CHAT_STORAGE_KEY);
  };

  const handleSend = async () => {
    if (!message.trim()) {
      toast.error("Please type a clinical question or prompt.");
      return;
    }

    const newUserMessage: ChatMessage = {
      id: makeId(),
      role: "user",
      text: message.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((current) => [...current, newUserMessage]);
    setMessage("");
    setIsSending(true);

    const payload: ChatPayload = { message: newUserMessage.text };
    if (selectedPatient) {
      payload.patient_context = {
        id: selectedPatient.id,
        first_name: selectedPatient.first_name,
        last_name: selectedPatient.last_name,
        age: selectedPatient.age,
        gender: selectedPatient.gender,
        allergies: selectedPatient.allergies || [],
        current_medications: selectedPatient.current_medications || [],
        medical_history: selectedPatient.medical_history || {},
      };
    }
    if (symptoms.trim()) payload.symptoms = symptoms.split(",").map((s) => s.trim()).filter(Boolean);
    if (medications.trim()) payload.medications = medications.split(",").map((s) => s.trim()).filter(Boolean);
    if (allergies.trim()) payload.allergies = allergies.split(",").map((s) => s.trim()).filter(Boolean);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const resp = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!resp.ok || !resp.body) throw new Error("Streaming response not available");

      // create assistant message placeholder
      const assistantId = makeId();
      const assistantMessage: ChatMessage = { id: assistantId, role: "assistant", text: "", timestamp: new Date().toISOString(), sources: [] };
      setMessages((current) => [...current, assistantMessage]);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let sBuffer = "";

      // periodic flush to reduce re-render flicker
      const flush = () => {
        if (!assistantBufferRef.current) return;
        const chunk = assistantBufferRef.current;
        assistantBufferRef.current = "";
        setMessages((current) => current.map((m) => (m.id === assistantId ? { ...m, text: m.text + chunk } : m)));
      };
      flushTimerRef.current = window.setInterval(flush, 120);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        sBuffer += decoder.decode(value, { stream: true });

        let parts = sBuffer.split("\n\n");
        sBuffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line) continue;
          if (!line.startsWith("data:")) continue;
          const payloadText = line.replace(/^data:\s*/, "");
          try {
            const obj = JSON.parse(payloadText);
            if (obj.type === "chunk") {
              assistantBufferRef.current += obj.text;
            } else if (obj.type === "done") {
              setClinicalSummary(obj.clinical_summary ?? null);
              if (obj.follow_up_suggestions?.length) {
                setFollowUpSuggestions(obj.follow_up_suggestions);
                setMessages((current) =>
                  current.map((m) =>
                    m.id === assistantId
                      ? { ...m, followUpSuggestions: obj.follow_up_suggestions, clinicalIntelligence: obj.clinical_intelligence ?? undefined }
                      : m
                  )
                );
              }
              if (obj.sources || obj.cited_sources) {
                setMessages((current) => current.map((m) => (m.id === assistantId ? { ...m, sources: obj.sources, citedSources: obj.cited_sources } : m)));
              }
            }
          } catch {
            // ignore parse errors
          }
        }
      }

      // final flush and cleanup
      if (flushTimerRef.current) {
        window.clearInterval(flushTimerRef.current);
        flushTimerRef.current = null;
      }
      if (assistantBufferRef.current) {
        setMessages((current) => current.map((m) => (m.id === assistantId ? { ...m, text: m.text + assistantBufferRef.current } : m)));
        assistantBufferRef.current = "";
      }

      toast.success("AI assistant replied successfully.");

      // persist conversation
      try {
        if (selectedPatient) {
          const nowStr = new Date().toISOString();
          const allMessages = [...messages, { id: assistantId, role: "assistant" as const, text: "", timestamp: nowStr }].map((m) => ({ role: m.role, text: m.text, timestamp: m.timestamp }));
          await storeConversation({ patient_id: selectedPatient.id, title: `Chat ${new Date().toLocaleString()}`, messages: allMessages });
          if (selectedPatientId) conversationsQuery.refetch?.();
        }
      } catch {}
    } catch (error: any) {
      if (error?.name === "AbortError") {
        toast("Generation stopped.");
      } else {
        toast.error("Unable to send your question. Check your connection and try again.");
        // mark last assistant as error
        setMessages((current) => current.map((m, i) => (i === current.length - 1 && m.role === "assistant" ? { ...m, error: true } : m)));
      }
    } finally {
      setIsSending(false);
      abortControllerRef.current = null;
    }
  };

  const handlePromptClick = (prompt: string) => {
    setMessage(prompt);
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsSending(false);
    }
  };

  const handleRetry = (failedMessage: ChatMessage) => {
    // load previous user message into input and resend
    const idx = messages.findIndex((m) => m.id === failedMessage.id);
    if (idx > 0) {
      const prev = messages[idx - 1];
      if (prev && prev.role === "user") {
        setMessage(prev.text);
        // remove failed assistant message
        setMessages((current) => current.filter((m) => m.id !== failedMessage.id));
        setTimeout(() => handleSend(), 50);
      }
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied response");
    } catch {
      toast.error("Copy failed");
    }
  };

  // auto-scroll when messages update
  useEffect(() => {
    try {
      const el = containerRef.current;
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      }
    } catch {}
  }, [messages.length, isSending]);

  return (
    <div className="space-y-10">
      <PageHeading
        title="AI Medical Assistant"
        description="Use patient context, symptoms and clinical prompts to get fast, evidence-informed guidance from MediGenie."
      />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
            <Card title="Saved conversations">
              {selectedPatientId ? (
                conversationsQuery.isLoading ? (
                  <p className="text-sm text-slate-500">Loading conversations…</p>
                ) : savedConversations.length ? (
                  <div className="space-y-3">
                    {savedConversations.map((c: any) => (
                      <div key={c.id} className="rounded-3xl border border-slate-200 bg-white p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-slate-900">{c.title || `Conversation ${c.id}`}</p>
                            <p className="text-sm text-slate-500">{new Date(c.created_at).toLocaleString()}</p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                // load conversation messages into the UI
                                const msgs: ChatMessage[] = c.messages.map((m: any) => ({ id: `stored-${m.id}`, role: m.role, text: m.text, timestamp: m.timestamp }));
                                setMessages(msgs);
                                setClinicalSummary(null);
                              }}
                              className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                            >
                              Load
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No saved conversations for this patient.</p>
                )
              ) : (
                <p className="text-sm text-slate-500">Select a patient to view saved conversations.</p>
              )}
            </Card>
          <Card title="Clinical conversation">
            <div className="flex flex-col gap-4">
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm text-slate-500">
                  Ask questions about diagnosis, treatment planning, medication safety, or workflow next steps. Your selected patient profile will be used to provide more relevant clinical context.
                </p>
              </div>

              <div className="min-h-[420px] overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-inner">
                <div className="flex h-full flex-col overflow-hidden">
                  <div ref={containerRef} className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-100">
                    {messages.length === 0 ? (
                      <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
                        <p className="text-lg font-semibold text-slate-900">Begin the chat with a clinical question</p>
                        <p className="mt-2 text-sm">Your messages and assistant responses will appear here.</p>
                      </div>
                    ) : (
                      messages.map((item) => (
                        <div
                          key={item.id}
                          className={`flex ${item.role === "assistant" ? "justify-start" : "justify-end"}`}
                        >
                          <div
                            className={`max-w-[85%] rounded-[2rem] p-5 shadow-sm ${
                              item.role === "assistant"
                                ? "bg-white text-slate-900 border border-slate-200"
                                : "bg-brand-600 text-white"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.2em] text-slate-500">
                              <span>{item.role === "assistant" ? "MediGenie Assistant" : "You"}</span>
                              <span>{formatTime(item.timestamp)}</span>
                            </div>
                            <div className="mt-3 whitespace-pre-wrap text-sm leading-6">
                              {item.role === "assistant" ? (
                                <div className="space-y-3">
                                  <div className="rounded-2xl bg-slate-50 p-4 text-sm leading-7 text-slate-800 border border-slate-100">
                                    {item.text.split(/\n{2,}/).map((paragraph, index) => {
                                      // Render basic bold syntax **text**, inline code, and [Source] citations
                                      const parts = paragraph.split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\])/g);
                                      return (
                                        <p key={index} className="mt-3 first:mt-0">
                                          {parts.map((part, i) => {
                                            if (part.startsWith("**") && part.endsWith("**")) {
                                              return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
                                            }
                                            if (part.startsWith("`") && part.endsWith("`")) {
                                              return <code key={i} className="rounded bg-slate-200 px-1.5 py-0.5 font-mono text-xs text-brand-700">{part.slice(1, -1)}</code>;
                                            }
                                            if (part.startsWith("[") && part.endsWith("]")) {
                                              return <span key={i} className="ml-1 inline-flex items-center rounded bg-brand-50 px-1.5 py-0.5 text-[10px] font-medium text-brand-700 ring-1 ring-inset ring-brand-600/20">{part.slice(1, -1)}</span>;
                                            }
                                            return part;
                                          })}
                                        </p>
                                      );
                                    })}
                                  </div>
                                  <div className="mt-2 flex items-center gap-2">
                                    <button onClick={() => handleCopy(item.text)} className="text-xs text-slate-500 hover:text-slate-700">Copy</button>
                                    {item.error ? (
                                      <button onClick={() => handleRetry(item)} className="text-xs text-red-600">Retry</button>
                                    ) : (
                                      <button onClick={() => handleRetry(item)} className="text-xs text-slate-500">Regenerate</button>
                                    )}
                                  </div>
                                  {item.citedSources?.length ? (
                                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                                      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-500 mb-3">
                                        <BookOpen className="h-4 w-4" />
                                        Sources cited
                                      </div>
                                      <ul className="space-y-3">
                                        {item.citedSources.map((source, idx) => (
                                          <li key={idx} className="text-sm text-slate-700">
                                            <span className="font-medium text-slate-900">{idx + 1}. {source.name}</span>
                                            <span className="text-slate-500 ml-2">&mdash; "{source.excerpt}..."</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  ) : item.sources?.length ? (
                                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs uppercase tracking-[0.2em] text-slate-500">
                                      <div className="flex items-center gap-2">
                                        <BookOpen className="h-4 w-4" />
                                        Sources: {item.sources.join(", ")}
                                      </div>
                                    </div>
                                  ) : null}
                                </div>
                              ) : (
                                <p>{item.text}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                    {isSending ? (
                      <div className="flex justify-start">
                        <div className="max-w-[70%] rounded-[2rem] bg-white border border-slate-200 p-4 shadow-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-slate-500 mr-2">MediGenie is thinking</span>
                            <div className="flex space-x-1">
                              <div className="h-2 w-2 animate-bounce rounded-full bg-brand-500 [animation-delay:-0.3s]" />
                              <div className="h-2 w-2 animate-bounce rounded-full bg-brand-500 [animation-delay:-0.15s]" />
                              <div className="h-2 w-2 animate-bounce rounded-full bg-brand-500" />
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </div>

                  <div className="border-t border-slate-200 bg-white p-6">
                    <label htmlFor="assistant-message" className="sr-only">
                      Clinical question
                    </label>
                    <textarea
                      id="assistant-message"
                      rows={4}
                      value={message}
                      onChange={(event) => setMessage(event.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          if (!isSending) handleSend();
                        }
                      }}
                      className="w-full resize-none rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                      placeholder="Type a clinical question, such as ‘What is the next step for this patient?’"
                    />
                    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex flex-wrap gap-2 text-sm text-slate-500">
                        <span>{selectedPatient ? `${selectedPatient.first_name} ${selectedPatient.last_name}` : "No patient selected"}</span>
                        <span className="text-slate-300">•</span>
                        <span>{selectedPatient ? `${selectedPatient.age} years · ${selectedPatient.gender}` : "Use the patient sidebar to add context."}</span>
                      </div>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          onClick={handleConversationReset}
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                        >
                          Reset conversation
                        </button>
                        {isSending ? (
                          <button type="button" onClick={handleStop} className="inline-flex items-center justify-center rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white">Stop</button>
                        ) : (
                          <button
                            type="button"
                            onClick={handleSend}
                            disabled={isSending}
                            className="inline-flex items-center justify-center rounded-2xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                          >
                            Send to assistant
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Latest clinical summary">
            <p className="text-sm text-slate-600">
              The assistant will show a concise summary here when clinical context is available.
            </p>
            <div className="mt-4 min-h-[110px] rounded-3xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
              {clinicalSummary ? (
                <p className="whitespace-pre-wrap">{clinicalSummary}</p>
              ) : (
                <p className="text-slate-500">No summary available yet. Ask a question to generate one.</p>
              )}
            </div>
          </Card>

          {followUpSuggestions.length > 0 && (
            <Card title="Suggested follow-up questions">
              <p className="text-sm text-slate-600">
                Context-aware follow-ups generated from your last clinical query.
              </p>
              <div className="mt-4 grid gap-2">
                {followUpSuggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setMessage(suggestion)}
                    className="rounded-3xl border border-brand-200 bg-brand-50 px-4 py-3 text-left text-sm text-brand-700 transition hover:border-brand-400 hover:bg-brand-100"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card title="Patient context">
            <div className="space-y-4">
              <div>
                <label htmlFor="patient-select" className="block text-sm font-medium text-slate-700">
                  Select patient profile
                </label>
                <select
                  id="patient-select"
                  value={selectedPatientId ?? ""}
                  onChange={(event) => setSelectedPatientId(event.target.value ? Number(event.target.value) : null)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                >
                  <option value="">No patient selected</option>
                  {patients.map((patient: Patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.first_name} {patient.last_name} · ID {patient.id}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="symptoms" className="block text-sm font-medium text-slate-700">
                    Symptoms
                  </label>
                  <input
                    id="symptoms"
                    type="text"
                    value={symptoms}
                    onChange={(event) => setSymptoms(event.target.value)}
                    placeholder="Fever, chest pain, fatigue"
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  />
                </div>
                <div>
                  <label htmlFor="medications" className="block text-sm font-medium text-slate-700">
                    Medications
                  </label>
                  <input
                    id="medications"
                    type="text"
                    value={medications}
                    onChange={(event) => setMedications(event.target.value)}
                    placeholder="Aspirin, Lisinopril"
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  />
                </div>
                <div>
                  <label htmlFor="allergies" className="block text-sm font-medium text-slate-700">
                    Allergies
                  </label>
                  <input
                    id="allergies"
                    type="text"
                    value={allergies}
                    onChange={(event) => setAllergies(event.target.value)}
                    placeholder="Penicillin, latex"
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  />
                </div>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                <p className="font-semibold text-slate-900">Patient record details</p>
                {selectedPatient ? (
                  <div className="mt-3 space-y-2 text-sm text-slate-700">
                    <p>{selectedPatient.first_name} {selectedPatient.last_name}</p>
                    <p>ID {selectedPatient.id}</p>
                    <p>Age {selectedPatient.age} · {selectedPatient.gender}</p>
                    <p>Medications: {selectedPatient.current_medications?.join(", ") || "None listed"}</p>
                    <p>Allergies: {selectedPatient.allergies?.join(", ") || "None listed"}</p>
                  </div>
                ) : (
                  <p className="mt-3 text-slate-500">Choose a patient above to include clinical context in your chat.</p>
                )}
              </div>
            </div>
          </Card>

          <Card title="Quick clinical prompts">
            <div className="space-y-3">
              <p className="text-sm text-slate-600">Jump-start the conversation with common medical review prompts.</p>
              <div className="grid gap-3">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    type="button"
                    key={prompt}
                    onClick={() => handlePromptClick(prompt)}
                    className="rounded-3xl border border-slate-200 bg-white px-4 py-4 text-left text-sm text-slate-700 transition hover:border-brand-400 hover:bg-slate-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </Card>

          <Card title="Conversation tools">
            <div className="space-y-3 text-sm text-slate-600">
              <div className="flex items-center gap-2 rounded-2xl bg-brand-50 p-3 text-brand-700">
                <Sparkles className="h-4 w-4" />
                <span>Saved conversations are stored locally for quick continuation.</span>
              </div>
              <div className="flex items-center gap-2 rounded-2xl bg-slate-50 p-3">
                <MessageSquareQuote className="h-4 w-4 text-slate-500" />
                <span>Suggested prompts help you move from triage to treatment planning quickly.</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
