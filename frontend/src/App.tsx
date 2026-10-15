import { useEffect, useState } from "react";
import { AppShell, type View } from "./components/AppShell";
import { clearToken, getHealth, getMe, logout } from "./lib/api";
import { LandingView } from "./views/LandingView";
import { WorkspaceView } from "./views/WorkspaceView";

function App() {
  const [screen, setScreen] = useState<"landing" | "workspace">("landing");
  const [view, setView] = useState<View>("overview");
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  useEffect(() => { getHealth().then((online) => setApiStatus(online ? "online" : "offline")).catch(() => setApiStatus("offline")); }, []);
  useEffect(() => { if (localStorage.getItem("resumeiq.access_token")) getMe().then(() => setScreen("workspace")).catch(() => { clearToken(); }); }, []);
  if (screen === "landing") return <LandingView onAuthenticated={() => setScreen("workspace")} />;
  return <AppShell view={view} onNavigate={setView} apiStatus={apiStatus} onLogout={() => { void logout(); setScreen("landing"); setView("overview"); }}><WorkspaceView view={view} onNavigate={setView} /></AppShell>;
}

export default App;
