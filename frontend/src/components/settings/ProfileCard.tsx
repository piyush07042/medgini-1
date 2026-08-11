import { useState, useRef } from "react";
import Card from "../../components/Card";
import type { User } from "../../types/api";
import { updateProfile, uploadAvatar, getProfile } from "../../api/settings";
import { useAuthStore } from "../../store/authStore";

export default function ProfileCard({ user }: { user: User | null }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(user?.full_name || "");
  const [editEmail, setEditEmail] = useState(user?.email || "");
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const setUser = useAuthStore((state) => state.setUser);

  const displayName = user?.full_name || user?.email || "Guest";
  const initial = displayName.charAt(0).toUpperCase() || "U";

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateProfile({ full_name: editName, email: editEmail });
      const res = await getProfile();
      if (res.data) setUser(res.data as User);
      setIsEditing(false);
    } catch (e) {
      console.error("Failed to update profile", e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadAvatar(file);
      const res = await getProfile();
      if (res.data) setUser(res.data as User);
    } catch (e) {
      console.error("Failed to upload avatar", e);
    }
  };

  return (
    <Card title="Profile">
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <div 
            className="group relative flex h-16 w-16 cursor-pointer items-center justify-center overflow-hidden rounded-3xl bg-brand-100 text-2xl font-semibold text-brand-700 hover:bg-brand-200"
            onClick={() => fileInputRef.current?.click()}
          >
            {user?.avatar_url ? (
              <img src={`http://localhost:8000${user.avatar_url}`} alt="Avatar" className="h-full w-full object-cover" />
            ) : (
              initial
            )}
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
              <span className="text-xs text-white">Upload</span>
            </div>
            <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleAvatarChange} />
          </div>
          <div>
            <p className="text-lg font-semibold text-slate-900">{displayName}</p>
            <p className="text-sm text-slate-500">{user ? user.email : "No authenticated user"}</p>
          </div>
        </div>

        {isEditing ? (
          <div className="space-y-4 rounded-3xl border border-brand-200 bg-brand-50/30 p-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Name</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Email</label>
              <input
                type="email"
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div className="flex gap-2">
              <button 
                onClick={handleSave} 
                disabled={isSaving}
                className="rounded-2xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
              <button 
                onClick={() => setIsEditing(false)} 
                className="rounded-2xl bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-300"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Name</p>
                <p className="mt-2 text-sm font-semibold text-slate-900">{user?.full_name || "Unavailable"}</p>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Role</p>
                <p className="mt-2 text-sm font-semibold text-slate-900">{user?.role || "Unavailable"}</p>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <button 
                onClick={() => setIsEditing(true)}
                className="w-full rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200"
              >
                Edit profile
              </button>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
