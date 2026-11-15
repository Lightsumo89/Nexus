import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import type { Game } from "../types";
import GameCard from "../components/GameCard";

export default function MyGames() {
  const games = useQuery({
    queryKey: ["my-games"],
    queryFn: () => api<Game[]>("/me/games"),
    refetchInterval: 5000,
  });

  const now = Date.now();
  const all = games.data ?? [];

  const upcoming = all
    .filter(
      (game) =>
        game.status !== "cancelled" &&
        new Date(game.starts_at).getTime() >= now - 2 * 3600_000
    )
    .reverse();

  const pending = upcoming.filter(
    (game) => game.status === "host_transfer_pending"
  );

  const active = upcoming.filter(
    (game) => game.status === "active"
  );

  const past = all.filter(
    (game) =>
      game.status === "cancelled" ||
      new Date(game.starts_at).getTime() < now - 2 * 3600_000
  );

  return (
    <div className="stack">
      <h1>Your games</h1>

      <h2>Awaiting a new host</h2>
      {pending.length === 0 && (
        <p className="muted">No games awaiting a new host.</p>
      )}
      {pending.map((game) => (
        <GameCard key={game.id} game={game} />
      ))}

      <h2>Upcoming</h2>
      {active.length === 0 && (
        <p className="muted">Nothing booked yet.</p>
      )}
      {active.map((game) => (
        <GameCard key={game.id} game={game} />
      ))}

      <h2>Past and cancelled</h2>
      {past.length === 0 && (
        <p className="muted">No past games.</p>
      )}
      {past.map((game) => (
        <GameCard key={game.id} game={game} />
      ))}
    </div>
  );
}