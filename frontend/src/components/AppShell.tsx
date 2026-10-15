import { type ReactNode } from "react";
import { motion } from "framer-motion";
import { Activity, BarChart3, BriefcaseBusiness, FileText, Gauge, Lightbulb, MessageSquareText, Network, Settings2, Sparkles } from "lucide-react";

type View = "overview" | "resumes" | "jobs" | "analysis" | "skills" | "recommendations" | "interview" | "system-design" | "settings";

type AppShellProps = { view: View; onNavigate: (view: View) => void; apiStatus: "checking" | "online" | "offline"; onLogout: () => void; children: ReactNode };

const links: { id: View; label: string; icon: typeof Gauge }[] = [
  { id: "overview", label: "Overview", icon: Gauge },
  { id: "resumes", label: "Resume library", icon: FileText },
  { id: "jobs", label: "Job descriptions", icon: BriefcaseBusiness },
  { id: "analysis", label: "Analysis", icon: BarChart3 },
  { id: "skills", label: "Skill map", icon: Activity },
  { id: "recommendations", label: "Recommendations", icon: Lightbulb },
  { id: "interview", label: "Interview prep", icon: MessageSquareText },
  { id: "system-design", label: "System design", icon: Network },
];

export function AppShell({ view, onNavigate, apiStatus, onLogout, children }: AppShellProps) {
  return (
    <motion.div className="product-shell" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}>
      <aside className="product-sidebar">
        <button className="product-brand" type="button" onClick={() => onNavigate("overview")} aria-label="Go to ResumeIQ overview">
          <span className="brand-mark"><Sparkles size={16} /></span><span><b>ResumeIQ</b><small>evidence workspace</small></span>
        </button>
        <p className="nav-label">Workspace</p>
        <nav className="product-nav" aria-label="Product navigation">
          {links.map(({ id, label, icon: Icon }) => <motion.button className={view === id ? "selected" : ""} key={id} type="button" onClick={() => onNavigate(id)} whileHover={{ x: 3 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}><Icon size={16} /><span>{label}</span></motion.button>)}
        </nav>
        <div className="sidebar-bottom">
          <button className={view === "settings" ? "selected" : ""} type="button" onClick={() => onNavigate("settings")}><Settings2 size={16} /><span>Settings</span></button>
          <div className="connection"><span className={`connection-dot ${apiStatus}`} /> API {apiStatus}</div>
          <div className="account-line"><span className="avatar">JD</span><span>Jordan Doe</span><small>Free</small></div>
        </div>
      </aside>
      <section className="product-main">
        <header className="product-topbar"><div className="mobile-brand"><span className="brand-mark"><Sparkles size={14} /></span><b>ResumeIQ</b></div><div className="topbar-path">Workspace <span>/</span> {links.find((link) => link.id === view)?.label ?? "Settings"}</div><button className="profile-button" type="button" aria-label="Sign out" onClick={onLogout}>JD</button></header>
        {children}
      </section>
    </motion.div>
  );
}

export type { View };
