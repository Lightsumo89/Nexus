import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, fmtWhen, WEEKDAYS } from "../api";
import type { Invite } from "../types";

function describe(i: Invite) {
  if (i.game) return `Game at ${i.game.court.name}, ${fmtWhen(i.game.starts_at)}`;
  if (i.league) return `League: ${i.league.name}, ${WEEKDAYS[i.league.weekday]} ${i.league.time}`;
  return "Note";
}

export default function Invites() {
  const qc = useQueryClient();
  const data = useQuery({ queryKey: ["invites"], queryFn: () => api<{ received: Invite[]; sent: Invite[] }>("/invites") });
  const respond = useMutation({
    mutationFn: ({ id, action }: { id: number; action: "accept" | "decline" }) => api(`/invites/${id}/${action}`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invites"] });
      qc.invalidateQueries({ queryKey: ["games"] });
      qc.invalidateQueries({ queryKey: ["my-games"] });
    },
  });
  return (
    <div className="stack">
      <h1>Invites</h1>
      <h2>Received</h2>
      {(data.data?.received ?? []).length === 0 && <p className="muted">No invites.</p>}
      {(data.data?.received ?? []).map((i) => (
        <div className="card" key={i.id}>
          <div>
            <Link to={`/u/${i.sender.handle}`}>
              <strong>{i.sender.display_name}</strong>
            </Link>{" "}
            invited you
          </div>
          <div className="muted">{describe(i)}</div>
          {i.note && <p>{i.note}</p>}
          {i.status === "pending" ? (
            <div className="two">
              <button onClick={() => respond.mutate({ id: i.id, action: "accept" })}>Accept</button>
              <button className="ghost" onClick={() => respond.mutate({ id: i.id, action: "decline" })}>
                Decline
              </button>
            </div>
          ) : (
            <span className="tag">{i.status}</span>
          )}
          {respond.error && <p className="error">{respond.error.message}</p>}
        </div>
      ))}
      <h2>Sent</h2>
      {(data.data?.sent ?? []).length === 0 && <p className="muted">Nothing sent.</p>}
      {(data.data?.sent ?? []).map((i) => (
        <div className="card" key={i.id}>
          <div>
            To <Link to={`/u/${i.recipient.handle}`}>{i.recipient.display_name}</Link> · <span className="tag">{i.status}</span>
          </div>
          <div className="muted">{describe(i)}</div>
        </div>
      ))}
    </div>
  );
}
