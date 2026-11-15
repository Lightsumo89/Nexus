import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { useMe } from "../hooks";
import ProfileForm from "../components/ProfileForm";

export default function Settings() {
  const { data: me } = useMe();
  const nav = useNavigate();
  const qc = useQueryClient();
  const leave = async () => {
    qc.clear();
    nav("/");
  };
  const logout = useMutation({ mutationFn: () => api("/auth/logout", { method: "POST" }), onSuccess: leave });
  const remove = useMutation({ mutationFn: () => api("/me", { method: "DELETE" }), onSuccess: leave });
  if (!me?.profile) return null;
  return (
    <div className="stack">
      <h1>Settings</h1>
      <p className="muted">Signed in as {me.email}</p>
      <ProfileForm initial={me.profile} submitLabel="Save changes" onDone={() => nav(`/u/${me.profile?.handle}`)} />
      <button className="ghost" onClick={() => logout.mutate()}>
        Log out
      </button>
      <button className="link danger" onClick={() => window.confirm("Delete your account and all your data? This can’t be undone.") && remove.mutate()}>
        Delete my account
      </button>
    </div>
  );
}
