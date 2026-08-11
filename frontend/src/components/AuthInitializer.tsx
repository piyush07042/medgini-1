import { useEffect } from "react";
import { useAuthStore } from "../store/authStore";

export default function AuthInitializer({ children }: { children: React.ReactNode }) {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  return <>{children}</>; 
}
