"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import {
  BarChart3,
  Home,
  LogOut,
  Trophy,
  Users,
  TrendingUp,
  History,
  Info,
  Zap,
  Swords,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/predict", label: "Predict", icon: Zap },
  { href: "/players", label: "Players", icon: Users },
  { href: "/leaderboard", label: "Leaderboard", icon: TrendingUp },
  { href: "/tournaments", label: "Tournaments", icon: Trophy },
  { href: "/simulate", label: "Simulate", icon: Swords },
  { href: "/history", label: "History", icon: History },
  { href: "/about", label: "About", icon: Info },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [hovered, setHovered] = useState(false);
  const { user, logout } = useAuth();

  const expanded = hovered;

  return (
    <aside
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        "sticky top-0 h-screen bg-sidebar flex flex-col border-r border-sidebar-border transition-[width] duration-200 overflow-hidden",
        expanded ? "w-60" : "w-16"
      )}
    >
      {/* Logo */}
      <div className="px-3 py-5 border-b border-sidebar-border">
        <Link
          href="/"
          className={cn(
            "flex items-center gap-2.5",
            !expanded && "justify-center"
          )}
        >
          <BarChart3 className="h-6 w-6 shrink-0 text-primary" />
          {expanded && (
            <span className="font-black text-base tracking-tight whitespace-nowrap uppercase">
              Tennis<span className="text-primary">Predictor</span>
            </span>
          )}
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive =
            pathname === href ||
            (href !== "/" && pathname.startsWith(href + "/"));
          return (
            <Link
              key={href}
              href={href}
              title={!expanded ? label : undefined}
              className={cn(
                "relative flex items-center gap-3 py-2.5 text-sm font-medium transition-all whitespace-nowrap rounded-sm",
                expanded ? "px-3" : "justify-center px-0",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-semibold"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
              )}
            >
              {/* Active left-border indicator */}
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-0.5 bg-primary rounded-r-full" />
              )}
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-primary" : ""
                )}
              />
              {expanded && label}
            </Link>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-2 pb-2 border-t border-sidebar-border pt-2">
        {expanded && user && (
          <div className="px-3 py-1.5 mb-1">
            <p className="text-xs font-medium text-sidebar-foreground truncate">{user.username}</p>
            <p className="text-[10px] text-sidebar-foreground/50 truncate">{user.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          title={!expanded ? "Logout" : undefined}
          className={cn(
            "w-full flex items-center gap-3 py-2.5 text-sm font-medium rounded-sm text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground transition-all",
            expanded ? "px-3" : "justify-center px-0"
          )}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {expanded && "Logout"}
        </button>
      </div>

      {/* Footer */}
      {expanded && (
        <div className="px-6 py-4 border-t border-sidebar-border">
          <p className="text-[10px] text-sidebar-foreground/60 whitespace-nowrap uppercase tracking-widest">
            ATP 2000–2025 · XGBoost + Elo
          </p>
        </div>
      )}
    </aside>
  );
}
