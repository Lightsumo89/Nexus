
import { Link } from "react-router-dom";

export const APP_NAME = "Pickup";

export default function Landing() {
  return (
    <div className="landing">
      <header className="row">
        <strong>{APP_NAME}</strong>
        <Link to="/login">Log in</Link>
      </header>

      <section className="hero">
        <h1>Find a pickup game near you, tonight.</h1>
        <p>
          See which courts have games scheduled, reserve a spot, and
          organize your own. No group chat required.
        </p>

        <Link className="button" to="/signup">
          Create your account
        </Link>

        <p className="muted">You must be 18 or older.</p>
      </section>

      <section className="grid3">
        <div className="card">
          <h3>Browse courts</h3>
          <p>Hours, distance and who plays where.</p>
        </div>

        <div className="card">
          <h3>Reserve a spot</h3>
          <p>Join a game and see who else is in.</p>
        </div>

        <div className="card">
          <h3>Host and invite</h3>
          <p>Post a game, invite people you play with.</p>
        </div>
      </section>
    </div>
  );
}
