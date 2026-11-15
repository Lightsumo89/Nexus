import { Navigate, useNavigate } from "react-router-dom";
import { useMe } from "../hooks";
import ProfileForm from "../components/ProfileForm";

export default function Onboarding() {
  const nav = useNavigate();
  const { data: me } = useMe();
  if (me?.profile) return <Navigate to="/explore" replace />;
  const suggested = (me?.email.split("@")[0] ?? "").toLowerCase().replace(/[^a-z0-9_]/g, "").slice(0, 30);
  return (
    <div className="auth">
      <h1>Set up your profile</h1>
      <p className="muted">This is what other players see. You can change it any time.</p>
      <ProfileForm suggestedHandle={suggested} submitLabel="Finish" onDone={() => nav("/explore")} />
    </div>
  );
}
