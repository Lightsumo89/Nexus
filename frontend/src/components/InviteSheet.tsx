import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, fmtWhen } from "../api";
import type { Game, Invite, League } from "../types";

export default function InviteSheet({ handle, onClose }: { handle: string; onClose: () => void }) {
  const [kind, setKind] = useState<"game" | "league" | "note">("note");
  const [target, setTarget] = useState("");
  const [note, setNote] = useState("");
  const games = useQuery({ queryKey: ["my-games"], queryFn: () => api<Game[]>("/me/games") });
  const leagues = useQuery({ queryKey: ["my-leagues"], queryFn: () => api<League[]>("/leagues?organizing=true") });
  const hosted = (games.data ?? []).filter((g) => g.hosted && new Date(g.starts_at) > new Date());
  const send = useMutation({
    mutationFn: () =>
      api<Invite>("/invites", {
        body: {
          recipient_handle: handle,
          kind,
          game_id: kind === "game" ? Number(target) : null,
          league_id: kind === "league" ? Number(target) : null,
          note: note || null,
        },
      }),
  });
  return (
    <div className="sheet" onClick={onClose}>
      <div className="sheet-body" onClick={(e) => e.stopPropagation()}>
        <h2>Invite @{handle}</h2>
        <div className="seg">
          {(["note", "game", "league"] as const).map((k) => (
            <button key={k} className={kind === k ? "on" : ""} onClick={() => { setKind(k); setTarget(""); }}>
              {k === "note" ? "Quick note" : k === "game" ? "Game" : "League"}
            </button>
          ))}
        </div>
        {kind === "game" && (
          <label>
            Which game
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">Choose one of your games</option>
              {hosted.map((g) => (
                <option key={g.id} value={g.id}>
                  {fmtWhen(g.starts_at)} · {g.court.name}
                </option>
              ))}
            </select>
          </label>
        )}
        {kind === "league" && (
          <label>
            Which league
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">Choose a league you organize</option>
              {(leagues.data ?? []).map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          {kind === "note" ? "Note" : "Add a note (optional)"}
          <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={200} rows={3} />
        </label>
        {send.error && <p className="error">{send.error.message}</p>}
        {send.isSuccess ? (
          <p className="ok">Invite sent.</p>
        ) : (
          <button disabled={send.isPending || (kind !== "note" && !target)} onClick={() => send.mutate()}>
            Send invite
          </button>
        )}
        <button className="ghost" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
