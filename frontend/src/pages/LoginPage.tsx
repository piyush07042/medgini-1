import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { loginSchema } from "../utils/validation";
import { useAuthStore } from "../store/authStore";
import type { LoginFormValues } from "../types/form";
import FormField from "../components/FormField";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setFormError(null);
    try {
      await login({ email: data.email, password: data.password, rememberMe });
      toast.success("Logged in successfully");
      navigate("/");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Login failed. Please check your credentials.";
      setFormError(message);
      toast.error(message);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid w-full overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-soft lg:grid-cols-[1.05fr_0.95fr]">
        <div className="bg-gradient-to-br from-brand-600 to-brand-800 p-8 text-white sm:p-10 lg:p-12">
          <div className="max-w-md space-y-6">
            <div className="inline-flex rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm font-medium backdrop-blur">Secure clinical access</div>
            <div className="space-y-3">
              <h1 className="text-3xl font-semibold leading-tight">Welcome back to MediGenie</h1>
              <p className="text-sm text-brand-100">Access patient risk workflows, intelligence insights, and secure medical operations from one dashboard.</p>
            </div>
            <div className="rounded-2xl border border-white/20 bg-white/10 p-4 text-sm text-brand-50 backdrop-blur">
              <p className="font-medium">Need an account?</p>
              <p className="mt-1 text-brand-100">Register to start managing care pathways and AI-supported reports.</p>
            </div>
          </div>
        </div>

        <div className="p-8 sm:p-10 lg:p-12">
          <div className="mx-auto max-w-md space-y-8">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Sign in</h2>
              <p className="mt-2 text-sm text-slate-500">Use your email and password to continue securely.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {formError ? <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{formError}</div> : null}
              <FormField label="Email or username" type="email" placeholder="you@example.com" register={register("email")} error={errors.email} />

              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700" htmlFor="password">Password</label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    {...register("password")}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-12 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                  />
                  <button
                    type="button"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute inset-y-0 right-3 flex items-center text-slate-500"
                    onClick={() => setShowPassword((value) => !value)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password ? <p className="text-xs text-red-600">{errors.password.message}</p> : null}
              </div>

              <div className="flex items-center justify-between gap-3 text-sm">
                <label className="flex items-center gap-2 text-slate-600">
                  <input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
                  <span>Remember me</span>
                </label>
                <button type="button" onClick={() => alert("Forgot Password functionality coming soon.")} className="text-brand-600 hover:text-brand-700">Forgot password?</button>
              </div>

              <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300">
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {isSubmitting ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <div className="text-center text-sm text-slate-500">
              New here? <Link to="/register" className="font-semibold text-brand-600 hover:text-brand-700">Create an account</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
