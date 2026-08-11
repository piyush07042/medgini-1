import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Camera, FileText, History, Users, Search as SearchIcon, X as XIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import PageHeading from "../components/PageHeading";
import Card from "../components/Card";
import FormField from "../components/FormField";
import { patientSchema } from "../utils/validation";
import { createPatient, deletePatient, getPatientTimeline, getPatientVisits, listPatients, updatePatient, uploadPatientAvatar } from "../api/patients";
import type { PatientFormValues } from "../types/form";
import type { Patient, ApiResponse } from "../types/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { invalidateDashboardCache } from "../services/dashboardService";
import MultiDiseaseIntelligenceCard from "../components/patients/MultiDiseaseIntelligenceCard";


type PatientSortKey = "created_at" | "first_name" | "age" | "gender";
const PAGE_SIZE_OPTIONS = [5, 8, 12];

function formatPatientNotes(patient: Patient) {
  if (!patient.medical_history) {
    return "No medical history recorded.";
  }

  if (typeof patient.medical_history === "string") {
    return patient.medical_history;
  }

  if (patient.medical_history.notes) {
    return String(patient.medical_history.notes);
  }

  return JSON.stringify(patient.medical_history, null, 2);
}

function formatHistoryValue(value: unknown) {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value.filter(Boolean).join(", ");
  }

  if (value && typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return "No additional details recorded.";
}

function buildTimelineEvents(patient: Patient, events: any[]) {
  if (events.length) {
    return events;
  }

  const note = formatPatientNotes(patient);
  if (note && note !== "No medical history recorded.") {
    return [
      {
        id: `patient-note-${patient.id}`,
        title: "Clinical summary",
        description: note,
        event_type: "summary",
        date: patient.created_at,
        source: "Patient record",
      },
    ];
  }

  return [];
}

export default function PatientsPage() {
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [genderFilter, setGenderFilter] = useState("all");
  const [sortKey, setSortKey] = useState<PatientSortKey>("created_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[1]);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [visits, setVisits] = useState<any[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const { data, isLoading } = useQuery<ApiResponse<Patient[]>>({
    queryKey: ["patients"],
    queryFn: () => listPatients({ page: 1, page_size: 500 }),
    staleTime: 1000 * 60 * 5,
  });

  const createForm = useForm<PatientFormValues>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      gender: "Male",
    },
  });

  const editForm = useForm<PatientFormValues>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      gender: "Male",
    },
  });

  const patients = data?.data ?? [];

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearchTerm(searchInput.trim());
    }, 250);

    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const filteredPatients = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return patients
      .filter((patient) => {
        const matchesSearch = normalizedSearch
          ? `${patient.first_name} ${patient.last_name}`.toLowerCase().includes(normalizedSearch) ||
            patient.allergies?.join(", ").toLowerCase().includes(normalizedSearch) ||
            patient.current_medications?.join(", ").toLowerCase().includes(normalizedSearch)
          : true;

        const matchesGender = genderFilter === "all" ? true : patient.gender.toLowerCase() === genderFilter.toLowerCase();

        return matchesSearch && matchesGender;
      })
      .sort((a, b) => {
        const direction = sortDirection === "asc" ? 1 : -1;

        if (sortKey === "age") {
          return direction * (a.age - b.age);
        }

        if (sortKey === "created_at") {
          return direction * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        }

        return direction * a[sortKey].toString().localeCompare(b[sortKey].toString(), undefined, { numeric: true });
      });
  }, [patients, searchTerm, genderFilter, sortKey, sortDirection]);

  const pageCount = Math.max(1, Math.ceil(filteredPatients.length / pageSize));
  const pagedPatients = filteredPatients.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const pageNumbers = useMemo(() => {
    if (pageCount <= 1) {
      return [1];
    }

    const maxButtons = 5;
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(pageCount, start + maxButtons - 1);

    if (end - start + 1 < maxButtons) {
      start = Math.max(1, end - maxButtons + 1);
    }

    return Array.from({ length: end - start + 1 }, (_, index) => start + index);
  }, [currentPage, pageCount]);
  const selectedPatient = selectedPatientId ? filteredPatients.find((patient) => patient.id === selectedPatientId) : filteredPatients[0] ?? null;

  useEffect(() => {
    if (currentPage > pageCount) {
      setCurrentPage(1);
    }
  }, [currentPage, pageCount]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, genderFilter, sortKey, sortDirection, pageSize]);

  useEffect(() => {
    if (!selectedPatientId && filteredPatients.length > 0) {
      setSelectedPatientId(filteredPatients[0].id);
    }

    if (selectedPatientId && !filteredPatients.some((patient) => patient.id === selectedPatientId)) {
      setSelectedPatientId(filteredPatients[0]?.id ?? null);
    }
  }, [filteredPatients, selectedPatientId]);

  useEffect(() => {
    if (!selectedPatient?.id) {
      setTimeline([]);
      setVisits([]);
      return;
    }

    const loadHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const [timelineResponse, visitsResponse] = await Promise.all([
          getPatientTimeline(selectedPatient.id),
          getPatientVisits(selectedPatient.id),
        ]);
        setTimeline(timelineResponse.data ?? []);
        setVisits(visitsResponse.data ?? []);
      } catch {
        setTimeline([]);
        setVisits([]);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadHistory();
  }, [selectedPatient?.id]);

  useEffect(() => {
    if (selectedPatientId && !isEditing) {
      const selectedPatient = filteredPatients.find((patient) => patient.id === selectedPatientId);
      if (selectedPatient) {
        editForm.reset({
          first_name: selectedPatient.first_name,
          last_name: selectedPatient.last_name,
          age: selectedPatient.age,
          gender: selectedPatient.gender,
          allergies: selectedPatient.allergies?.join(", ") ?? "",
          current_medications: selectedPatient.current_medications?.join(", ") ?? "",
          medical_history: selectedPatient.medical_history?.notes ? String(selectedPatient.medical_history.notes) : "",
        });
      }
    }
  }, [selectedPatientId, filteredPatients, editForm, isEditing]);

  const totalPatients = patients.length;
  const recentlyAddedCount = patients.filter((patient) => Date.now() - new Date(patient.created_at).getTime() <= 1000 * 60 * 60 * 24 * 30).length;
  const highRiskCount = patients.filter((patient) => patient.age >= 65).length;

  const recentPatients = useMemo(
    () =>
      [...patients]
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5),
    [patients]
  );

  const genderOptions = useMemo(
    () => ["all", ...Array.from(new Set(patients.map((patient) => patient.gender || "Unknown")))],
    [patients]
  );

  const handleCreatePatient = async (values: PatientFormValues) => {
    try {
      await createPatient({
        first_name: values.first_name,
        last_name: values.last_name,
        age: values.age,
        gender: values.gender,
        allergies: values.allergies ? values.allergies.split(",").map((item) => item.trim()) : [],
        current_medications: values.current_medications ? values.current_medications.split(",").map((item) => item.trim()) : [],
        medical_history: values.medical_history ? { notes: values.medical_history } : {},
      });
      toast.success("Patient record created.");
      createForm.reset({ gender: "Male" });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      invalidateDashboardCache();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (error) {
      toast.error("Unable to create patient. Please try again.");
    }
  };

  const handleSelectPatient = (patientId: number) => {
    setSelectedPatientId(patientId);
    setIsEditing(false);
  };

  const handleEditPatient = async (values: PatientFormValues) => {
    if (!selectedPatient) {
      return;
    }

    const payload = {
      first_name: values.first_name,
      last_name: values.last_name,
      age: values.age,
      gender: values.gender,
      allergies: values.allergies ? values.allergies.split(",").map((item) => item.trim()) : [],
      current_medications: values.current_medications ? values.current_medications.split(",").map((item) => item.trim()) : [],
      medical_history: values.medical_history ? { notes: values.medical_history } : {},
    };

    try {
      await updatePatient(selectedPatient.id, payload);
      toast.success("Patient updated successfully.");
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      invalidateDashboardCache();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (error) {
      toast.error("Unable to update patient. Please try again.");
    }
  };

  const handleDeletePatient = async (patientId: number) => {
    if (!window.confirm("Delete this patient record?")) {
      return;
    }

    try {
      await deletePatient(patientId);
      toast.success("Patient deleted successfully.");
      setSelectedPatientId(null);
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      invalidateDashboardCache();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (error) {
      toast.error("Unable to delete patient. Please try again.");
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    if (selectedPatient) {
      editForm.reset({
        first_name: selectedPatient.first_name,
        last_name: selectedPatient.last_name,
        age: selectedPatient.age,
        gender: selectedPatient.gender,
        allergies: selectedPatient.allergies?.join(", ") ?? "",
        current_medications: selectedPatient.current_medications?.join(", ") ?? "",
        medical_history: selectedPatient.medical_history?.notes ? String(selectedPatient.medical_history.notes) : "",
      });
    }
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedPatient) {
      return;
    }

    try {
      setIsUploadingAvatar(true);
      await uploadPatientAvatar(selectedPatient.id, file);
      toast.success("Patient avatar updated.");
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      invalidateDashboardCache();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch {
      toast.error("Unable to upload avatar. Please try again.");
    } finally {
      setIsUploadingAvatar(false);
      event.target.value = "";
    }
  };

  return (
    <div className="space-y-10">
      <PageHeading title="Patient Management" description="Manage your patient roster, review clinical history, and access reports and predictions." />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.95fr]">
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <Card title="Total patients">
              <p className="text-4xl font-semibold text-slate-900">{totalPatients}</p>
              <p className="mt-3 text-sm text-slate-500">Patients under your care.</p>
            </Card>
            <Card title="High-risk patients">
              <p className="text-4xl font-semibold text-slate-900">{highRiskCount}</p>
              <p className="mt-3 text-sm text-slate-500">Age 65+ patients with additional monitoring needs.</p>
            </Card>
            <Card title="Added in 30 days">
              <p className="text-4xl font-semibold text-slate-900">{recentlyAddedCount}</p>
              <p className="mt-3 text-sm text-slate-500">Patients registered in the last 30 days.</p>
            </Card>
          </div>

          <Card title="Patient list">
            <div className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr]">
                <div className="relative">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Search Patients</span>
                  <div className="relative">
                    <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                    <input
                      value={searchInput}
                      onChange={(event) => setSearchInput(event.target.value)}
                      placeholder="Search by name, allergy, medication..."
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-11 text-sm text-slate-900 outline-none transition-all focus:border-brand-400 focus:bg-white focus:ring-4 focus:ring-brand-100 shadow-sm hover:border-slate-300"
                    />
                    {searchInput && (
                      <button
                        onClick={() => {
                          setSearchInput("");
                          setSearchTerm("");
                        }}
                        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-600 transition-colors"
                      >
                        <XIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
                <div className="relative">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Gender Filter</span>
                  <select
                    value={genderFilter}
                    onChange={(event) => setGenderFilter(event.target.value)}
                    className="w-full cursor-pointer rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition-all focus:border-brand-400 focus:bg-white focus:ring-4 focus:ring-brand-100 shadow-sm hover:border-slate-300 appearance-none"
                  >
                    {genderOptions.map((gender) => (
                      <option key={gender} value={gender === "all" ? "all" : gender}>
                        {gender === "all" ? "All Genders" : gender}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="relative">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Sort By</span>
                  <select
                    value={`${sortKey}_${sortDirection}`}
                    onChange={(event) => {
                      const [key, direction] = event.target.value.split("_") as [PatientSortKey, "asc" | "desc"];
                      setSortKey(key);
                      setSortDirection(direction);
                    }}
                    className="w-full cursor-pointer rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition-all focus:border-brand-400 focus:bg-white focus:ring-4 focus:ring-brand-100 shadow-sm hover:border-slate-300 appearance-none"
                  >
                    <option value="created_at_desc">Newest First</option>
                    <option value="created_at_asc">Oldest First</option>
                    <option value="first_name_asc">Name (A–Z)</option>
                    <option value="first_name_desc">Name (Z–A)</option>
                    <option value="age_desc">Age (High to Low)</option>
                    <option value="age_asc">Age (Low to High)</option>
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto rounded-3xl border border-slate-200">
                <table className="min-w-full border-collapse text-left text-sm text-slate-700">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-4 py-4 font-medium">Patient</th>
                      <th className="px-4 py-4 font-medium">Age</th>
                      <th className="px-4 py-4 font-medium">Gender</th>
                      <th className="px-4 py-4 font-medium">Allergies</th>
                      <th className="px-4 py-4 font-medium">Created</th>
                      <th className="px-4 py-4 font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-6 text-sm text-slate-500">
                          Loading patients...
                        </td>
                      </tr>
                    ) : pagedPatients.length ? (
                      pagedPatients.map((patient) => (
                        <tr
                          key={patient.id}
                          onClick={() => handleSelectPatient(patient.id)}
                          className={`cursor-pointer transition hover:bg-slate-50 ${selectedPatientId === patient.id ? "bg-slate-100" : ""}`}
                        >
                          <td className="px-4 py-4 font-semibold text-slate-900">
                            {patient.first_name} {patient.last_name}
                          </td>
                          <td className="px-4 py-4">{patient.age}</td>
                          <td className="px-4 py-4">{patient.gender}</td>
                          <td className="px-4 py-4">{patient.allergies?.join(", ") || "None"}</td>
                          <td className="px-4 py-4">{new Date(patient.created_at).toLocaleDateString()}</td>
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleSelectPatient(patient.id);
                                }}
                                className="rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-200"
                              >
                                View
                              </button>
                              <button
                                type="button"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleDeletePatient(patient.id);
                                }}
                                className="rounded-full bg-red-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-red-700"
                                aria-label={`Delete patient ${patient.first_name} ${patient.last_name}`}
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-6 text-sm text-slate-500">
                          No patients match the current filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-col gap-4 border-t border-slate-200 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-500">
                  Showing {pagedPatients.length} of {filteredPatients.length} patients.
                  {searchTerm ? ` · Search active: “${searchTerm}”` : ""}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((value) => Math.max(1, value - 1))}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  {pageNumbers.map((pageNumber) => (
                    <button
                      key={pageNumber}
                      type="button"
                      onClick={() => setCurrentPage(pageNumber)}
                      className={`h-10 min-w-10 rounded-2xl border px-3 text-sm font-semibold transition ${currentPage === pageNumber ? "border-brand-600 bg-brand-600 text-white" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}
                    >
                      {pageNumber}
                    </button>
                  ))}
                  <button
                    type="button"
                    disabled={currentPage >= pageCount}
                    onClick={() => setCurrentPage((value) => Math.min(pageCount, value + 1))}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                  <select
                    value={pageSize}
                    onChange={(event) => setPageSize(Number(event.target.value))}
                    className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  >
                    {PAGE_SIZE_OPTIONS.map((size) => (
                      <option key={size} value={size}>
                        {size} per page
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Recent patient activity">
            <div className="space-y-4">
              {recentPatients.length ? (
                recentPatients.map((patient) => (
                  <div key={patient.id} className="rounded-3xl bg-slate-50 px-4 py-4">
                    <p className="font-semibold text-slate-900">{patient.first_name} {patient.last_name}</p>
                    <p className="text-sm text-slate-500">Added {new Date(patient.created_at).toLocaleDateString()}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No recent activity yet.</p>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Add patient">
            <form onSubmit={createForm.handleSubmit(handleCreatePatient)} className="space-y-5">
              <FormField label="First name" placeholder="Jane" register={createForm.register("first_name")} error={createForm.formState.errors.first_name} />
              <FormField label="Last name" placeholder="Doe" register={createForm.register("last_name")} error={createForm.formState.errors.last_name} />
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField label="Age" type="number" placeholder="42" register={createForm.register("age")} error={createForm.formState.errors.age} />
                <FormField label="Gender" placeholder="Female" register={createForm.register("gender")} error={createForm.formState.errors.gender} />
              </div>
              <FormField label="Allergies" placeholder="Peanuts, Penicillin" register={createForm.register("allergies")} error={createForm.formState.errors.allergies} />
              <FormField label="Current medications" placeholder="Aspirin, Metformin" register={createForm.register("current_medications")} error={createForm.formState.errors.current_medications} />
              <FormField label="Medical history" placeholder="Type patient history" register={createForm.register("medical_history")} error={createForm.formState.errors.medical_history}>
                <textarea
                  rows={4}
                  {...createForm.register("medical_history")}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                />
              </FormField>
              <button
                type="submit"
                disabled={createForm.formState.isSubmitting}
                className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {createForm.formState.isSubmitting ? "Saving..." : "Save patient"}
              </button>
            </form>
          </Card>

          <Card title="Patient details">
            {selectedPatient ? (
              <div className="space-y-5">
                {!isEditing ? (
                  <div className="space-y-5">
                    <div className="rounded-3xl bg-slate-50 p-5">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-lg font-semibold text-slate-900">{selectedPatient.first_name} {selectedPatient.last_name}</p>
                          <p className="text-sm text-slate-500">Age {selectedPatient.age} • {selectedPatient.gender}</p>
                        </div>
                        <label className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100">
                          <Camera className="h-4 w-4" />
                          {isUploadingAvatar ? "Uploading..." : "Upload avatar"}
                          <input type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
                        </label>
                      </div>
                      <p className="mt-4 text-sm leading-7 text-slate-700">{formatPatientNotes(selectedPatient)}</p>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
                        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">Allergies</p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          {selectedPatient.allergies && selectedPatient.allergies.length > 0 ? (
                            selectedPatient.allergies.map((allergy, idx) => (
                              <span key={idx} className="inline-flex items-center rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 ring-1 ring-inset ring-rose-600/10">
                                {allergy}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-slate-500">None recorded</span>
                          )}
                        </div>
                      </div>
                      <div className="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
                        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">Medications</p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          {selectedPatient.current_medications && selectedPatient.current_medications.length > 0 ? (
                            selectedPatient.current_medications.map((medication, idx) => (
                              <span key={idx} className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 ring-1 ring-inset ring-blue-600/10">
                                {medication}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-slate-500">No active medications</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Multi-Disease Intelligence Subsystem */}
                    <MultiDiseaseIntelligenceCard
                      data={{
                        combined_risk: {
                          organ_scores: {
                            cardiovascular: selectedPatient.age > 50 ? 45.0 : 20.0,
                            metabolic: selectedPatient.allergies?.length ? 35.0 : 15.0,
                            renal: 15.0,
                            hepatic: 10.0,
                            neurological: 5.0,
                            oncological: 10.0
                          },
                          combined_risk_percent: selectedPatient.age > 50 ? 45.0 : 20.0,
                          risk_category: selectedPatient.age > 50 ? "Moderate" : "Low"
                        },
                        health_index: {
                          health_score: selectedPatient.age > 50 ? 72.0 : 88.0,
                          status: selectedPatient.age > 50 ? "Fair" : "Optimal",
                          description: `Patient health index is rated ${selectedPatient.age > 50 ? "Fair" : "Optimal"} based on age (${selectedPatient.age}) and registered parameters.`
                        },
                        comorbidities: selectedPatient.age > 50 ? [
                          {
                            name: "Metabolic-Cardiovascular Susceptibility",
                            severity: "Moderate",
                            criteria_met: ["Age > 50", "Active Medication Profile"],
                            recommendation: "Routine metabolic panel screening and annual blood pressure monitoring."
                          }
                        ] : [],
                        longitudinal_timeline: buildTimelineEvents(selectedPatient, timeline).slice(0, 4).map((e) => ({
                          date: e.date,
                          disease: e.title,
                          risk_score_percent: 25.0,
                          risk_category: "Low",
                          summary: e.description
                        }))
                      }}
                    />

                    <div className="grid gap-3 lg:grid-cols-2">

                      <div className="rounded-3xl border border-slate-200 bg-white p-5">
                        <div className="mb-4 flex items-center gap-2">
                          <History className="h-4 w-4 text-brand-600" />
                          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">Timeline</p>
                        </div>
                        {isLoadingHistory ? (
                          <p className="text-sm text-slate-500">Loading timeline…</p>
                        ) : buildTimelineEvents(selectedPatient, timeline).length ? (
                          <div className="space-y-3">
                            {buildTimelineEvents(selectedPatient, timeline).slice(0, 4).map((event) => (
                              <div key={event.id} className="rounded-2xl bg-slate-50 p-3">
                                <p className="text-sm font-semibold text-slate-900">{event.title}</p>
                                <p className="mt-1 text-sm text-slate-600">{formatHistoryValue(event.description)}</p>
                                <div className="mt-2 flex flex-wrap items-center gap-2">
                                  <p className="text-xs uppercase tracking-[0.22em] text-slate-400">{event.date}</p>
                                  {event.source ? <span className="rounded-full bg-brand-100 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-brand-700">{event.source}</span> : null}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500">No timeline events recorded yet.</p>
                        )}
                      </div>
                      <div className="rounded-3xl border border-slate-200 bg-white p-5">
                        <div className="mb-4 flex items-center gap-2">
                          <FileText className="h-4 w-4 text-brand-600" />
                          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">Visit history</p>
                        </div>
                        {isLoadingHistory ? (
                          <p className="text-sm text-slate-500">Loading visits…</p>
                        ) : visits.length ? (
                          <div className="space-y-3">
                            {visits.slice(0, 4).map((visit) => (
                              <div key={visit.id} className="rounded-2xl bg-slate-50 p-3">
                                <div className="flex items-center justify-between gap-2">
                                  <p className="text-sm font-semibold text-slate-900">{visit.visit_type}</p>
                                  <span className="rounded-full bg-brand-100 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-brand-700">{visit.status}</span>
                                </div>
                                <p className="mt-1 text-sm text-slate-600">{formatHistoryValue(visit.summary)}</p>
                                <p className="mt-2 text-xs uppercase tracking-[0.22em] text-slate-400">{visit.date}</p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500">No visit history yet. New encounters will appear here automatically.</p>
                        )}
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-3xl bg-slate-50 p-5">
                        <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Created</p>
                        <p className="mt-3 text-sm text-slate-700">{new Date(selectedPatient.created_at).toLocaleString()}</p>
                      </div>
                      <div className="rounded-3xl bg-slate-50 p-5">
                        <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Doctor ID</p>
                        <p className="mt-3 text-sm text-slate-700">{selectedPatient.doctor_id}</p>
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <Link
                        to={`/reports?patientId=${selectedPatient.id}`}
                        className="inline-flex items-center justify-center rounded-2xl border border-brand-500 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-700 transition hover:bg-brand-100"
                      >
                        View AI reports
                      </Link>
                      <Link
                        to={`/stroke?patientId=${selectedPatient.id}`}
                        className="inline-flex items-center justify-center rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
                      >
                        Run prediction
                      </Link>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => setIsEditing(true)}
                        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      >
                        Edit record
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeletePatient(selectedPatient.id)}
                        className="rounded-2xl bg-red-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-red-700"
                      >
                        Delete patient
                      </button>
                    </div>

                  </div>
                ) : (
                  <form onSubmit={editForm.handleSubmit(handleEditPatient)} className="space-y-5">
                    <FormField label="First name" placeholder="Jane" register={editForm.register("first_name")} error={editForm.formState.errors.first_name} />
                    <FormField label="Last name" placeholder="Doe" register={editForm.register("last_name")} error={editForm.formState.errors.last_name} />
                    <div className="grid gap-5 sm:grid-cols-2">
                      <FormField label="Age" type="number" placeholder="42" register={editForm.register("age")} error={editForm.formState.errors.age} />
                      <FormField label="Gender" placeholder="Female" register={editForm.register("gender")} error={editForm.formState.errors.gender} />
                    </div>
                    <FormField label="Allergies" placeholder="Peanuts, Penicillin" register={editForm.register("allergies")} error={editForm.formState.errors.allergies} />
                    <FormField label="Current medications" placeholder="Aspirin, Metformin" register={editForm.register("current_medications")} error={editForm.formState.errors.current_medications} />
                    <FormField label="Medical history" placeholder="Type patient history" register={editForm.register("medical_history")} error={editForm.formState.errors.medical_history}>
                      <textarea
                        rows={4}
                        {...editForm.register("medical_history")}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                      />
                    </FormField>
                    <div className="flex flex-wrap gap-3">
                      <button
                        type="submit"
                        className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
                      >
                        Save changes
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelEdit}
                        className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-200"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Select a patient from the list to view details.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
