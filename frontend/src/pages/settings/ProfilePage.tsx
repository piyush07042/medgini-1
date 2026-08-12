import { useMemo, useState, useEffect } from "react";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";
import { useAuthStore } from "../../store/authStore";
import { getProfile, updateProfile, changePassword, uploadAvatar, listSessions, getLoginHistory } from "../../api/settings";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);

  const [editingName, setEditingName] = useState(user?.full_name ?? "");
  const [editingEmail, setEditingEmail] = useState(user?.email ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  useEffect(() => {
    setEditingName(user?.full_name ?? "");
    setEditingEmail(user?.email ?? "");
  }, [user]);

  const sessionsQuery = useQuery({ queryKey: ["sessions"], queryFn: () => listSessions(), enabled: Boolean(token) });
  const loginQuery = useQuery({ queryKey: ["loginHistory"], queryFn: () => getLoginHistory(), enabled: Boolean(token) });

  const setUser = useAuthStore((state) => state.setUser);

  const handleSaveProfile = async () => {
    try {
      await updateProfile({ full_name: editingName, email: editingEmail });
      const res = await getProfile();
      if (res.data) setUser(res.data);
      toast.success("Profile updated");
    } catch (e) {
      toast.error("Unable to update profile");
    }
  };

  const handleChangePassword = async () => {
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword });
      setCurrentPassword("");
      setNewPassword("");
      toast.success("Password changed");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Unable to change password");
    }
  };

  const handleUploadAvatar = async () => {
    if (!avatarFile) return;
    try {
      await uploadAvatar(avatarFile);
      const res = await getProfile();
      if (res.data) setUser(res.data);
      toast.success("Avatar uploaded");
    } catch {
      toast.error("Avatar upload failed");
    }
  };

  const sessionExpiry = useMemo(() => {
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.exp ? new Date(payload.exp * 1000).toLocaleString() : null;
    } catch {
      return null;
    }
  }, [token]);

  return (
    <div className="space-y-10">
      <PageHeading title="User profile" description="Review your authenticated account details and current browser session." />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <Card title="Account overview">
            <div className="space-y-5">
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm text-slate-500">Full name</p>
                <input value={editingName} onChange={(e) => setEditingName(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900" />
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm text-slate-500">Email address</p>
                <input value={editingEmail} onChange={(e) => setEditingEmail(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900" />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl border border-slate-200 bg-white p-5">
                  <p className="text-sm text-slate-500">Role</p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">{user?.role ?? "Not available"}</p>
                </div>
                <div className="rounded-3xl border border-slate-200 bg-white p-5">
                  <p className="text-sm text-slate-500">Account status</p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">{user ? "Active" : "Not signed in"}</p>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Session and security">
            <div className="space-y-4 text-sm text-slate-700">
              <p>
                <span className="font-semibold text-slate-900">Signed in:</span> {user ? "Yes" : "No"}
              </p>
              <p>
                <span className="font-semibold text-slate-900">Login source:</span> {typeof navigator !== "undefined" ? `${navigator.platform}` : "Browser"}
              </p>
              <p>
                <span className="font-semibold text-slate-900">Token expiry:</span> {sessionExpiry ?? "Unknown"}
              </p>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Profile actions">
            <div className="space-y-4 text-sm text-slate-600">
              <p>This page shows profile data from the authenticated session.</p>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Edit profile</p>
                <div className="mt-2 grid gap-3 sm:grid-cols-2">
                  <button onClick={handleSaveProfile} className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white">Save profile</button>
                  <button onClick={() => { setEditingName(user?.full_name ?? ""); setEditingEmail(user?.email ?? ""); }} className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold">Reset</button>
                </div>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Change password</p>
                <div className="mt-3 space-y-3">
                  <input type="password" placeholder="Current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3" />
                  <input type="password" placeholder="New password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3" />
                  <div className="flex gap-3">
                    <button onClick={handleChangePassword} className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white">Change password</button>
                  </div>
                </div>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Avatar upload</p>
                <div className="mt-3 space-y-3">
                  <input type="file" onChange={(e) => setAvatarFile(e.target.files?.[0] ?? null)} />
                  <button onClick={handleUploadAvatar} className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white">Upload avatar</button>
                </div>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Active sessions</p>
                {sessionsQuery.isLoading ? <p>Loading…</p> : sessionsQuery.data?.data?.length ? (
                  <ul className="mt-2 text-sm text-slate-600">
                    {sessionsQuery.data.data.map((s: any) => (
                      <li key={s.id}>{s.device} • last seen {new Date(s.last_seen).toLocaleString()}</li>
                    ))}
                  </ul>
                ) : <p className="mt-2 text-sm text-slate-500">No active sessions found.</p>}
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Recent login history</p>
                {loginQuery.isLoading ? <p>Loading…</p> : loginQuery.data?.data?.length ? (
                  <ul className="mt-2 text-sm text-slate-600">
                    {loginQuery.data.data.map((e: any) => (
                      <li key={e.id}>{e.device} • {new Date(e.created_at).toLocaleString()}</li>
                    ))}
                  </ul>
                ) : <p className="mt-2 text-sm text-slate-500">No recent logins found.</p>}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
