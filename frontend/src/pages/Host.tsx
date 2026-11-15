import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { SKILLS, SPORTS } from "../types";
import type { Court, Game } from "../types";

function AddCourt() {
  const qc = useQueryClient();
  const [f, setF] = useState({ name: "", sport: "basketball", address: "", lat: "", lng: "", opens: "", closes: "" });
  const set = (k: keyof typeof f, v: string) => setF({ ...f, [k]: v });
  const add = useMutation({
    mutationFn: () =>
      api<Court>("/courts", {
        body: {
          name: f.name,
          sport: f.sport,
          address: f.address || null,
          lat: f.lat ? Number(f.lat) : null,
          lng: f.lng ? Number(f.lng) : null,
          opens: f.opens || null,
          closes: f.closes || null,
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["courts"] });
      setF({ name: "", sport: "basketball", address: "", lat: "", lng: "", opens: "", closes: "" });
    },
  });
  const here = () =>
    navigator.geolocation?.getCurrentPosition((p) =>
      setF((x) => ({ ...x, lat: p.coords.latitude.toFixed(5), lng: p.coords.longitude.toFixed(5) })),
    );
  return (
    <details className="card">
      <summary>Add a court</summary>
      <div className="stack">
        <label>
          Name
          <input value={f.name} onChange={(e) => set("name", e.target.value)} />
        </label>
        <label>
          Sport
          <select value={f.sport} onChange={(e) => set("sport", e.target.value)}>
            {SPORTS.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Address
          <input value={f.address} onChange={(e) => set("address", e.target.value)} />
        </label>
        <div className="two">
          <label>
            Latitude
            <input value={f.lat} onChange={(e) => set("lat", e.target.value)} inputMode="decimal" />
          </label>
          <label>
            Longitude
            <input value={f.lng} onChange={(e) => set("lng", e.target.value)} inputMode="decimal" />
          </label>
          <label>
            Opens
            <input type="time" value={f.opens} onChange={(e) => set("opens", e.target.value)} />
          </label>
          <label>
            Closes
            <input type="time" value={f.closes} onChange={(e) => set("closes", e.target.value)} />
          </label>
        </div>
        {add.error && <p className="error">{add.error.message}</p>}
        {add.isSuccess && <p className="ok">Court added.</p>}
        <div className="two">
          <button type="button" className="ghost" onClick={here}>
            Use my location
          </button>
          <button type="button" disabled={add.isPending || f.name.length < 2} onClick={() => add.mutate()}>
            Add court
          </button>
        </div>
      </div>
    </details>
  );
}

export default function Host() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const courts = useQuery({ queryKey: ["courts", "all"], queryFn: () => api<Court[]>("/courts") });
  const [courtId, setCourtId] = useState("");
  const [when, setWhen] = useState("");
  const [spots, setSpots] = useState(10);
  const [min, setMin] = useState(6);
  const [skill, setSkill] = useState("casual");
  const [note, setNote] = useState("");
  const create = useMutation({
    mutationFn: () =>
      api<Game>("/games", {
        body: { court_id: Number(courtId), starts_at: new Date(when).toISOString(), spots, min_players: min, skill, note: note || null },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["games"] });
      qc.invalidateQueries({ queryKey: ["my-games"] });
      nav("/explore");
    },
  });
  const submit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };
  return (
    <div className="stack">
      <h1>Host a game</h1>
      <form className="stack" onSubmit={submit}>
        <label>
          Court
          <select value={courtId} onChange={(e) => setCourtId(e.target.value)} required>
            <option value="">Choose a court</option>
            {(courts.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Date and time
          <input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} required />
        </label>
        <div className="two">
          <label>
            Spots
            <input type="number" min={2} max={30} value={spots} onChange={(e) => setSpots(Number(e.target.value))} />
          </label>
          <label>
            Minimum to run
            <input type="number" min={2} max={30} value={min} onChange={(e) => setMin(Number(e.target.value))} />
          </label>
        </div>
        <label>
          Skill level
          <select value={skill} onChange={(e) => setSkill(e.target.value)}>
            {SKILLS.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Note (optional)
          <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={200} />
        </label>
        {create.error && <p className="error">{create.error.message}</p>}
        <button disabled={create.isPending}>Post game</button>
      </form>
      <AddCourt />
    </div>
  );
}
