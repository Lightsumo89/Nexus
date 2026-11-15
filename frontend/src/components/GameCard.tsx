
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, fmtWhen } from "../api";
import type { Game } from "../types";
import Avatar from "./Avatar";

export default function GameCard({ game }: { game: Game }) {
  const qc = useQueryClient();
  const [currentTime, setCurrentTime] = useState(Date.now());

  const pending = game.status === "host_transfer_pending";
  const cancelled = game.status === "cancelled";

  useEffect(() => {
    if (!pending || !game.transfer_expires_at) {
      return;
    }

    const interval = window.setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);

    return () => window.clearInterval(interval);
  }, [pending, game.transfer_expires_at]);

  const refreshGames = () => {
    qc.invalidateQueries({ queryKey: ["games"] });
    qc.invalidateQueries({ queryKey: ["my-games"] });
    qc.invalidateQueries({ queryKey: ["me"] });
  };

  const transferTime = game.transfer_expires_at
    ? new Date(game.transfer_expires_at).getTime()
    : null;

  const remainingSeconds =
    transferTime === null
      ? null
      : Math.max(0, Math.ceil((transferTime - currentTime) / 1000));

  useEffect(() => {
    if (pending && remainingSeconds === 0) {
      refreshGames();
    }
  }, [pending, remainingSeconds]);

  const joinLeave = useMutation({
    mutationFn: () =>
      api<Game>(`/games/${game.id}/join`, {
        method: game.joined ? "DELETE" : "POST",
      }),
    onSuccess: refreshGames,
  });

  const transfer = useMutation({
    mutationFn: () =>
      api<Game>(`/games/${game.id}/transfer`, { method: "POST" }),
    onSuccess: refreshGames,
  });

  const claim = useMutation({
    mutationFn: () =>
      api<Game>(`/games/${game.id}/claim`, { method: "POST" }),
    onSuccess: refreshGames,
  });

  const cancel = useMutation({
    mutationFn: () =>
      api<Game>(`/games/${game.id}`, { method: "DELETE" }),
    onSuccess: refreshGames,
  });

  const full = game.players >= game.spots;
  const needs = Math.max(0, game.min_players - game.players);

  return (
    <div className="card">
      <div className="row">
        <div>
          <strong>{fmtWhen(game.starts_at)}</strong>
          <div className="muted">
            {game.court.name} · {game.skill}
          </div>
        </div>

        {cancelled ? (
          <span className="tag">Cancelled</span>
        ) : pending ? (
          <span className="tag">Host transfer pending</span>
        ) : game.hosted ? (
          <span className="tag">Hosting</span>
        ) : (
          <button
            className={game.joined ? "ghost" : ""}
            disabled={joinLeave.isPending || (full && !game.joined)}
            onClick={() => joinLeave.mutate()}
          >
            {game.joined ? "Leave" : full ? "Full" : "Join"}
          </button>
        )}
      </div>

      <div className="muted">
        {game.players}/{game.spots} in ·{" "}
        {needs === 0 ? "game is on" : `needs ${needs} more`}
      </div>

      {game.note && <p>{game.note}</p>}

      <Link className="host" to={`/u/${game.host.handle}`}>
        <Avatar user={game.host} size={24} /> {game.host.display_name}
      </Link>

      {game.hosted && !cancelled && !pending && (
        <div className="row">
          <button
            className="ghost"
            disabled={joinLeave.isPending || !game.joined}
            onClick={() => joinLeave.mutate()}
          >
            Stop playing
          </button>

          <button
            className="ghost"
            disabled={transfer.isPending}
            onClick={() => {
              if (
                window.confirm(
                  "Transfer hosting to another participant?"
                )
              ) {
                transfer.mutate();
              }
            }}
          >
            Transfer hosting
          </button>

          <button
            className="ghost"
            disabled={cancel.isPending}
            onClick={() => {
              if (window.confirm("Cancel this game?")) {
                cancel.mutate();
              }
            }}
          >
            Cancel game
          </button>
        </div>
      )}

      {pending && (
        <div className="stack">
          <p className="muted">
            {remainingSeconds === null
              ? "Waiting for a new host."
              : remainingSeconds > 0
                ? `A participant can claim hosting. ${remainingSeconds} seconds remaining.`
                : "The transfer window has expired. The game is being updated."}
          </p>

          {game.joined && !game.hosted && (
            <button
              disabled={claim.isPending || remainingSeconds === 0}
              onClick={() => {
                if (
                  window.confirm("Take over as the host of this game?")
                ) {
                  claim.mutate();
                }
              }}
            >
              Claim hosting
            </button>
          )}
        </div>
      )}

      {cancelled && (
        <p className="muted">
          This game is no longer accepting participants.
        </p>
      )}

      {joinLeave.error && (
        <p className="error">{joinLeave.error.message}</p>
      )}

      {transfer.error && (
        <p className="error">{transfer.error.message}</p>
      )}

      {claim.error && <p className="error">{claim.error.message}</p>}

      {cancel.error && <p className="error">{cancel.error.message}</p>}
    </div>
  );
}
