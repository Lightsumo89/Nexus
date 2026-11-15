import { Route, Routes } from "react-router-dom";
import { RequireAuth, RequireProfile } from "./components/Guards";
import Shell from "./components/Shell";
import Landing from "./pages/Landing";
import { Forgot, Login, Reset, Signup, Verify } from "./pages/AuthPages";
import Onboarding from "./pages/Onboarding";
import Explore from "./pages/Explore";
import Host from "./pages/Host";
import MyGames from "./pages/MyGames";
import Invites from "./pages/Invites";
import ProfilePage from "./pages/ProfilePage";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/login" element={<Login />} />
      <Route path="/verify" element={<Verify />} />
      <Route path="/forgot" element={<Forgot />} />
      <Route path="/reset" element={<Reset />} />
      <Route element={<RequireAuth />}>
        <Route path="/onboarding" element={<Onboarding />} />
        <Route element={<RequireProfile />}>
          <Route element={<Shell />}>
            <Route path="/explore" element={<Explore />} />
            <Route path="/host" element={<Host />} />
            <Route path="/games" element={<MyGames />} />
            <Route path="/invites" element={<Invites />} />
            <Route path="/u/:handle" element={<ProfilePage />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
