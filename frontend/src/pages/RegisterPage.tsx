import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { z } from "zod";
import { registerSchema } from "../utils/validation";
import { register as registerUser } from "../services/authService";
import { useAuthStore } from "../store/authStore";
import type { RegisterFormValues } from "../types/form";
import FormField from "../components/FormField";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const registrationSchema = registerSchema.extend({
    confirmPassword: z.string().min(1, "Please confirm your password."),
  });

  const {
    register: registerField,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues & { confirmPassword: string }>({
    resolver: zodResolver(registrationSchema),
  });

  const password = watch("password") ?? "";

  const [formError, setFormError] = useState<string | null>(null);
  const login = useAuthStore((state) => state.login);

  const onSubmit = async (data: RegisterFormValues & { confirmPassword: string }) => {
    setFormError(null);

    if (data.password !== data.confirmPassword) {
      setFormError("Passwords do not match.");
      toast.error("Passwords do not match.");
      return;
    }

    try {
      await registerUser({ email: data.email, password: data.password, full_name: data.full_name });
      await login({ email: data.email, password: data.password });
      toast.success("Registration successful. Redirecting to dashboard...");
      navigate("/");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Registration failed. Try again.";
      setFormError(message);
      toast.error(message);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid w-full overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-soft lg:grid-cols-[0.95fr_1.05fr]">
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-8 text-white sm:p-10 lg:p-12">
          <div className="max-w-md space-y-6">
            <div className="inline-flex rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm font-medium backdrop-blur">Join MediGenie</div>
            <div className="space-y-3">
              <h1 className="text-3xl font-semibold leading-tight">Create a secure clinician account</h1>
              <p className="text-sm text-slate-300">Register to manage patient data, reports, and AI-assisted care workflows.</p>
            </div>
            <div className="rounded-2xl border border-white/20 bg-white/10 p-4 text-sm text-slate-200 backdrop-blur">
              <p className="font-medium">Password tips</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-300">
                <li>Use at least 8 characters.</li>
                <li>Mix letters, numbers, and symbols.</li>
                <li>Keep it unique to your organization.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="p-8 sm:p-10 lg:p-12">
          <div className="mx-auto max-w-md space-y-8">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Create account</h2>
              <p className="mt-2 text-sm text-slate-500">Get started with a professional medical operations workspace.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {formError ? <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{formError}</div> : null}
              <FormField label="Full name" placeholder="Jane Doe" register={registerField("full_name")} error={errors.full_name} />
              <FormField label="Email" type="email" placeholder="you@example.com" register={registerField("email")} error={errors.email} />

              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700" htmlFor="password">Password</label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    {...registerField("password")}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-12 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  />
                  <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} className="absolute inset-y-0 right-3 flex items-center text-slate-500" onClick={() => setShowPassword((value) => !value)}>
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password ? <p className="text-xs text-red-600">{errors.password.message}</p> : null}
                <p className="text-xs text-slate-500">Strength: {password.length >= 8 ? "Good" : "Add more characters"}</p>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700" htmlFor="confirmPassword">Confirm password</label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="••••••••"
                    {...registerField("confirmPassword")}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-12 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  />
                  <button type="button" aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"} className="absolute inset-y-0 right-3 flex items-center text-slate-500" onClick={() => setShowConfirmPassword((value) => !value)}>
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.confirmPassword ? <p className="text-xs text-red-600">{errors.confirmPassword.message}</p> : null}
              </div>

              <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300">
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {isSubmitting ? "Creating account..." : "Create account"}
              </button>
            </form>

            <div className="text-center text-sm text-slate-500">
              Already have an account? <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-700">Sign in</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
