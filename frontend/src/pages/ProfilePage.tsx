import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { PublicProfile } from "../types";
import Avatar from "../components/Avatar";
import InviteSheet from "../components/InviteSheet";

export default function ProfilePage() {
  const { handle = "" } = useParams();
  const qc = useQueryClient();
  const [inviting, setInviting] = useState(false);
  const profile = useQuery({ queryKey: ["profile", handle], queryFn: () => api<PublicProfile>(`/users/${handle}`), enabled: !!handle });
  const follow = useMutation({
    mutationFn: (following: boolean) => api(`/users/${handle}/follow`, { method: following ? "DELETE" : "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile", handle] }),
  });
  const block = useMutation({
    mutationFn: () => api(`/users/${handle}/block`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile", handle] }),
  });
  if (profile.isLoading) return <p className="muted">Loading…</p>;
  if (profile.error || !profile.data) return <p className="error">Profile not found.</p>;
  const p = profile.data;
  const rel = p.relationship;
  const s = p.stats;
  return (
    <div className="stack">
      <div className="row head">
        <Avatar user={p} size={72} />
        <div>
          <h1>{p.display_name}</h1>
          <div className="muted">
            @{p.handle}
            {p.home_area && ` · ${p.home_area}`}
          </div>
        </div>
      </div>
      {p.bio && <p>{p.bio}</p>}
      {rel.is_self ? (
        <Link className="button ghost" to="/settings">
          Edit profile
        </Link>
      ) : (
        <div className="two">
          <button className={rel.following ? "ghost" : ""} disabled={follow.isPending} onClick={() => follow.mutate(rel.following)}>
            {rel.following ? (rel.followed_by ? "Friends" : "Following") : rel.followed_by ? "Follow back" : "Follow"}
          </button>
          <button className="ghost" disabled={!rel.can_invite} onClick={() => setInviting(true)}>
            Invite
          </button>
        </div>
      )}
      {!rel.is_self && !rel.can_invite && <p className="muted">This player only takes invites from friends.</p>}
      <div className="stats">
        <div><b>{s.games_played}</b><span>played</span></div>
        <div><b>{s.games_hosted}</b><span>hosted</span></div>
        <div><b>{s.followers}</b><span>followers</span></div>
        <div><b>{s.following}</b><span>following</span></div>
        <div><b>{s.leagues_joined}</b><span>leagues</span></div>
        <div><b>{s.show_up_rate == null ? "–" : `${Math.round(s.show_up_rate * 100)}%`}</b><span>show-up</span></div>
      </div>
      <h2>Sports</h2>
      <div className="chips">
        {p.sports.length === 0 && <span className="muted">None listed</span>}
        {p.sports.map((x) => (
          <span className="chip static" key={x.sport}>
            {x.sport} · {x.skill}
          </span>
        ))}
      </div>
      <h2>Plays at</h2>
      {p.major_courts.length === 0 && <p className="muted">No games played in the last 90 days.</p>}
      {p.major_courts.map((c) => (
        <div className="card" key={c.id}>
          {c.name} <span className="muted">· {c.count} games</span>
        </div>
      ))}
      <h2>Favorite courts</h2>
      {p.favorite_courts.length === 0 && <p className="muted">None saved.</p>}
      {p.favorite_courts.map((c) => (
        <div className="card" key={c.id}>
          {c.name}
        </div>
      ))}
      {!rel.is_self && (
        <button className="link danger" onClick={() => window.confirm(`Block ${p.display_name}?`) && block.mutate()}>
          Block this player
        </button>
      )}
      {inviting && <InviteSheet handle={p.handle} onClose={() => setInviting(false)} />}
    </div>
  );
}
