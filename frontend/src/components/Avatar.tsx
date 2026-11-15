import type { Mini } from "../types";

export default function Avatar({ user, size = 40 }: { user: Pick<Mini, "display_name" | "avatar_url">; size?: number }) {
  const style = { width: size, height: size, fontSize: size * 0.42 };
  if (user.avatar_url) return <img className="avatar" style={style} src={user.avatar_url} alt="" />;
  return (
    <span className="avatar fallback" style={style}>
      {user.display_name.trim().charAt(0).toUpperCase()}
    </span>
  );
}
