
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { useCoords } from "../hooks";
import { SPORTS } from "../types";
import type { Court, Game } from "../types";
import GameCard from "../components/GameCard";
import CourtMap from "../components/CourtMap";

export default function Explore() {
  const qc = useQueryClient();
  const { coords, ask } = useCoords();
  const [sport, setSport] = useState<string>("basketball");
  const [courtId, setCourtId] = useState<number | null>(null);
  const [, bump] = useState(0);
  const courtsKey = ["courts", sport, coords?.lat, coords?.lng];

  const courts = useQuery({
    queryKey: courtsKey,
    queryFn: () => api<Court[]>(`/courts?sport=${sport}${coords ? `&lat=${coords.lat}&lng=${coords.lng}` : ""}`),
  });

  const games = useQuery({
    queryKey: ["games"],
    queryFn: () => api<Game[]>("/games"),
    refetchInterval: 5000,
  });

  const fav = useMutation({
    mutationFn: (c: Court) => api(`/me/favorites/${c.id}`, { method: c.is_favorite ? "DELETE" : "PUT" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["courts"] }),
  });

  const ids = new Set((courts.data ?? []).map((c) => c.id));
  const shown = (games.data ?? []).filter((g) => ids.has(g.court.id) && (!courtId || g.court.id === courtId));

  return (
    <div className="stack">
      <h1>Explore</h1>
      <div className="chips">
        {SPORTS.map((s) => (
          <button key={s} className={`chip ${sport === s ? "on" : ""}`} onClick={() => { setSport(s); setCourtId(null); }}>
            {s}
          </button>
        ))}
      </div>
      <h2>Games this week</h2>
      {games.isLoading && <p className="muted">Loading…</p>}
      {!games.isLoading && shown.length === 0 && <p className="muted">No games yet. Host one from the Host tab.</p>}
      {shown.map((g) => (
        <GameCard key={g.id} game={g} />
      ))}
      <h2>Find courts</h2>
      <CourtMap
        courts={courts.data ?? []}
        selectedCourtId={courtId}
        onSelectCourt={setCourtId}
      />
      <div className="row">
        <h2>Courts</h2>
        {!coords && (
          <button className="ghost small" onClick={() => ask(() => bump((n) => n + 1))}>
            Sort by distance
          </button>
        )}
      </div>
      {(courts.data ?? []).map((c) => (
        <div className={`card ${courtId === c.id ? "picked" : ""}`} key={c.id}>
          <div className="row">
            <button className="link strong" onClick={() => setCourtId(courtId === c.id ? null : c.id)}>
              {c.name}
            </button>
            <button className={`heart ${c.is_favorite ? "on" : ""}`} aria-label="Favorite" onClick={() => fav.mutate(c)}>
              ♥
            </button>
          </div>
          <div className="muted">
            {c.address ?? c.sport}
            {c.distance_mi != null && ` · ${c.distance_mi} mi`}
            {c.closes && ` · closes ${c.closes}`}
          </div>
        </div>
      ))}
    </div>
  );
}
