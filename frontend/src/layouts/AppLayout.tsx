import type { PropsWithChildren } from "react";
import { useEffect, useState } from "react";

import type { AppRoute } from "../App";
import { Sidebar } from "../components/common/Sidebar";

type AppLayoutProps = PropsWithChildren<{
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
}>;

const sidebarStorageKey = "all4health.sidebarCollapsed";

export function AppLayout({ children, currentRoute, onNavigate }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(sidebarStorageKey) === "true");

  useEffect(() => {
    localStorage.setItem(sidebarStorageKey, String(collapsed));
  }, [collapsed]);

  return (
    <div className={`app-shell ${collapsed ? "is-sidebar-collapsed" : ""}`}>
      <Sidebar
        collapsed={collapsed}
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        onToggle={() => setCollapsed((value) => !value)}
      />
      <div className="app-main">
        <main className="page-container">{children}</main>
      </div>
    </div>
  );
}
