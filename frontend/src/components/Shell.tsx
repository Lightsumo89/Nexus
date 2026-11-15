import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api";
import { useMe } from "../hooks";

function VerifyBanner() {
  const [token, setToken] = useState<string | null>(sessionStorage.getItem("pickup.devVerify"));
  const [sent, setSent] = useState(false);
  const resend = useMutation({
    mutationFn: () => api<{ dev_verify_token?: string }>("/auth/resend", { method: "POST" }),
    onSuccess: (d) => {
      setSent(true);
      if (d.dev_verify_token) setToken(d.dev_verify_token);
    },
  });
  return (
    <div className="banner">
      Verify your email to join and host games.{" "}
      {token && <Link to={`/verify?token=${token}`}>Verify now (dev)</Link>}{" "}
      <button className="link" onClick={() => resend.mutate()} disabled={resend.isPending}>
        {sent ? "Sent again" : "Resend email"}
      </button>
    </div>
  );
}

export default function Shell() {
  const { data: me } = useMe();
  const tabs = [
    { to: "/explore", label: "Explore" },
    { to: "/host", label: "Host" },
    { to: "/games", label: "Games" },
    { to: "/invites", label: "Invites" },
    { to: `/u/${me?.profile?.handle ?? ""}`, label: "Profile" },
  ];
  return (
    <div className="shell">
      {me && !me.email_verified && <VerifyBanner />}
      <main className="page">
        <Outlet />
      </main>
      <nav className="tabs">
        {tabs.map((t) => (
          <NavLink key={t.label} to={t.to} className={({ isActive }) => (isActive ? "on" : "")}>
            {t.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
