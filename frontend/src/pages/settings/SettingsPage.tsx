import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeading from "../../components/PageHeading";
import ProfileCard from "../../components/settings/ProfileCard";
import ThemeSettings from "../../components/settings/ThemeSettings";
import NotificationSettings from "../../components/settings/NotificationSettings";
import LanguageSettings from "../../components/settings/LanguageSettings";
import SessionCard from "../../components/settings/SessionCard";
import LoginHistoryCard from "../../components/settings/LoginHistoryCard";
import AccountInformation from "../../components/settings/AccountInformation";
import { useAuthStore } from "../../store/authStore";
import { changePassword } from "../../api/settings";

export default function SettingsPage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handlePasswordChange = async () => {
    setPasswordError("");
    setPasswordSuccess("");
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("Please fill in all fields.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }
    setIsChangingPassword(true);
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordSuccess("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || "Failed to change password.");
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <PageHeading title="Settings" description="Manage your MediGenie preferences, session details, and local client settings." />
        <button
          type="button"
          onClick={() => navigate("/settings/profile")}
          className="inline-flex items-center justify-center rounded-2xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          Open profile details
        </button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <ProfileCard user={user} />
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <h2 className="text-xl font-semibold text-slate-900">Security</h2>
            <p className="mt-2 text-sm text-slate-500">Update your account password.</p>
            {passwordError && <p className="mt-2 text-sm text-red-600">{passwordError}</p>}
            {passwordSuccess && <p className="mt-2 text-sm text-green-600">{passwordSuccess}</p>}
            <div className="mt-6 space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="current-password">
                  Current Password
                </label>
                <input
                  id="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                  placeholder="Current password"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="new-password">
                  New Password
                </label>
                <input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                  placeholder="New password"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="confirm-password">
                  Confirm Password
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                  placeholder="Confirm new password"
                />
              </div>
              <button 
                type="button" 
                onClick={handlePasswordChange}
                disabled={isChangingPassword}
                className="w-full rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50" 
              >
                {isChangingPassword ? "Changing..." : "Change Password"}
              </button>
            </div>
          </div>
          <ThemeSettings />
          <NotificationSettings />
          <LanguageSettings />
        </div>

        <div className="space-y-6">
          <SessionCard user={user} token={token} />
          <LoginHistoryCard user={user} />
          <AccountInformation user={user} />
        </div>
      </div>
    </div>
  );
}
