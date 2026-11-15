import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { InvitePolicy, Profile, SKILLS, SPORTS, Skill, Sport } from "../types";

interface Props {
  initial?: Profile | null;
  suggestedHandle?: string;
  submitLabel: string;
  onDone: () => void;
}

export default function ProfileForm({ initial, suggestedHandle = "", submitLabel, onDone }: Props) {
  const qc = useQueryClient();
  const [handle, setHandle] = useState(initial?.handle ?? suggestedHandle);
  const [name, setName] = useState(initial?.display_name ?? "");
  const [bio, setBio] = useState(initial?.bio ?? "");
  const [area, setArea] = useState(initial?.home_area ?? "");
  const [policy, setPolicy] = useState<InvitePolicy>(initial?.invite_policy ?? "friends");
  const [sports, setSports] = useState<Partial<Record<Sport, Skill>>>(
    Object.fromEntries((initial?.sports ?? []).map((s) => [s.sport, s.skill])),
  );
  const [file, setFile] = useState<File | null>(null);

  const save = useMutation({
    mutationFn: async () => {
      await api("/me/profile", {
        method: "PUT",
        body: {
          handle,
          display_name: name,
          bio: bio || null,
          home_area: area || null,
          invite_policy: policy,
          sports: Object.entries(sports).map(([sport, skill]) => ({ sport, skill })),
        },
      });
      if (file) {
        const form = new FormData();
        form.append("file", file);
        await api("/me/avatar", { form });
      }
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
      qc.invalidateQueries({ queryKey: ["profile"] });
      onDone();
    },
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    save.mutate();
  };

  return (
    <form className="stack" onSubmit={submit}>
      <label>
        Display name
        <input value={name} onChange={(e) => setName(e.target.value)} maxLength={60} required />
      </label>
      <label>
        Handle
        <input value={handle} onChange={(e) => setHandle(e.target.value.toLowerCase())} maxLength={30} pattern="[a-z0-9_]{3,30}" required />
      </label>
      <label>
        Profile photo
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      <label>
        Home area
        <input value={area} onChange={(e) => setArea(e.target.value)} maxLength={80} />
      </label>
      <label>
        Bio
        <textarea value={bio} onChange={(e) => setBio(e.target.value)} maxLength={160} rows={2} />
      </label>
      <fieldset>
        <legend>Sports you play</legend>
        {SPORTS.map((s) => (
          <div className="row sport" key={s}>
            <label className="check">
              <input
                type="checkbox"
                checked={s in sports}
                onChange={(e) => {
                  const next = { ...sports };
                  if (e.target.checked) next[s] = "casual";
                  else delete next[s];
                  setSports(next);
                }}
              />
              {s}
            </label>
            {s in sports && (
              <select value={sports[s]} onChange={(e) => setSports({ ...sports, [s]: e.target.value as Skill })}>
                {SKILLS.map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </select>
            )}
          </div>
        ))}
      </fieldset>
      <label>
        Who can invite you
        <select value={policy} onChange={(e) => setPolicy(e.target.value as InvitePolicy)}>
          <option value="anyone">Anyone</option>
          <option value="friends">Friends (people who follow each other)</option>
          <option value="nobody">Nobody</option>
        </select>
      </label>
      {save.error && <p className="error">{save.error.message}</p>}
      <button disabled={save.isPending}>{save.isPending ? "Saving…" : submitLabel}</button>
    </form>
  );
}
