import { Navigate, Outlet } from "react-router-dom";
import { useMe } from "../hooks";

export function Splash() {
  return <div className="splash">Loading…</div>;
}

export function RequireAuth() {
  const { data, isLoading } = useMe();
  if (isLoading) return <Splash />;
  if (!data) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function RequireProfile() {
  const { data } = useMe();
  if (data && !data.profile) return <Navigate to="/onboarding" replace />;
  return <Outlet />;
}
