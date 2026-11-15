
export const SPORTS = ["basketball", "soccer", "tennis", "pickleball", "volleyball", "other"] as const;
export const SKILLS = ["casual", "intermediate", "competitive"] as const;
export type Sport = (typeof SPORTS)[number];
export type Skill = (typeof SKILLS)[number];
export type InvitePolicy = "anyone" | "friends" | "nobody";

export interface SportSkill {
  sport: Sport;
  skill: Skill;
}

export interface Mini {
  handle: string;
  display_name: string;
  avatar_url: string | null;
}

export interface Profile extends Mini {
  bio: string | null;
  home_area: string | null;
  invite_policy: InvitePolicy;
  sports: SportSkill[];
}

export interface Me {
  id: number;
  email: string;
  email_verified: boolean;
  profile: Profile | null;
}

export interface CourtRef {
  id: number;
  name: string;
}

export interface Court extends CourtRef {
  sport: string;
  address: string | null;
  lat: number | null;
  lng: number | null;
  opens: string | null;
  closes: string | null;
  is_favorite: boolean;
  distance_mi: number | null;
}

export interface Game {
  id: number;
  court: CourtRef;
  host: Mini;
  starts_at: string;
  spots: number;
  min_players: number;
  skill: string;
  note: string | null;
  players: number;
  joined: boolean;
  hosted: boolean;
  status: "active" | "host_transfer_pending" | "cancelled";
  transfer_expires_at: string | null;
  cancelled_at: string | null;
}

export interface League {
  id: number;
  name: string;
  court: CourtRef;
  weekday: number;
  time: string;
  skill: string;
  organizer: Mini;
  members: number;
  joined: boolean;
}

export interface Stats {
  games_played: number;
  games_hosted: number;
  leagues_joined: number;
  followers: number;
  following: number;
  show_up_rate: number | null;
}

export interface PublicProfile extends Profile {
  stats: Stats;
  major_courts: { id: number; name: string; count: number }[];
  favorite_courts: CourtRef[];
  relationship: {
    is_self: boolean;
    following: boolean;
    followed_by: boolean;
    can_invite: boolean;
  };
}

export interface Invite {
  id: number;
  kind: "game" | "league" | "note";
  note: string | null;
  status: string;
  created_at: string;
  sender: Mini;
  recipient: Mini;
  game: Game | null;
  league: League | null;
}
