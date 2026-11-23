"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSyncExternalStore } from "react";
import { useI18n } from "@/components/i18n-provider";
import { clearSession, getSession } from "@/features/auth/services/auth-service";

const navItems = [
  { href: "/", label: "nav.overview", icon: "◌" },
  { href: "/audit", label: "nav.audit", icon: "⌁" },
];
const sidebarStorageKey = "fluxium_sidebar_collapsed";
const subscribeSidebar = (onStoreChange: () => void) => {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener("fluxium-sidebar-change", onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener("fluxium-sidebar-change", onStoreChange);
  };
};
const getSidebarSnapshot = () => window.localStorage.getItem(sidebarStorageKey) === "true";
const getSidebarServerSnapshot = () => false;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const session = useSyncExternalStore(() => () => undefined, getSession, () => null);
  const { t } = useI18n();
  const sidebarCollapsed = useSyncExternalStore(subscribeSidebar, getSidebarSnapshot, getSidebarServerSnapshot);
  const isActive = (href: string) => href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);

  const toggleSidebar = () => {
    window.localStorage.setItem(sidebarStorageKey, String(!sidebarCollapsed));
    window.dispatchEvent(new Event("fluxium-sidebar-change"));
  };
  if (pathname === "/login") return <>{children}</>;
  const logout = () => {
    clearSession();
    router.push("/login");
  };

  return (
    <div className={sidebarCollapsed ? "app-shell is-collapsed" : "app-shell"}>
      <aside className="sidebar">
        <div className="sidebar-top">
          <Link href="/" className="brand"><span className="brand-mark">F</span><span>fluxium<small>AI PRODUCT MANAGEMENT</small></span></Link>
          <button className="sidebar-toggle" type="button" aria-label={sidebarCollapsed ? t("shell.expandMenu") : t("shell.collapseMenu")} aria-expanded={!sidebarCollapsed} title={sidebarCollapsed ? t("shell.expandMenu") : t("shell.collapseMenu")} onClick={toggleSidebar}>{sidebarCollapsed ? "→" : "←"}</button>
        </div>
        <div className="context-selector"><span className="eyebrow">{t("shell.workspace")}</span><strong>{session?.workspaceIds[0] ?? t("shell.noWorkspace")}</strong><span className="context-meta">{session?.tenantId ?? t("shell.signInConnect")}</span></div>
        <nav aria-label={t("nav.overview")}>
          <Link className={isActive(navItems[0].href) ? "is-active" : undefined} aria-current={isActive(navItems[0].href) ? "page" : undefined} href={navItems[0].href}><span aria-hidden="true">{navItems[0].icon}</span><span className="nav-label">{t(navItems[0].label)}</span></Link>
          <div className="context-menu-group">
            <span className="eyebrow">{t("nav.workspace")}</span>
            <div className="context-menu-links">
              <Link className={isActive("/workspace/products") ? "is-active" : undefined} aria-current={isActive("/workspace/products") ? "page" : undefined} href="/workspace/products"><span aria-hidden="true">01</span><span className="nav-label">{t("workspace.productTitle")}</span></Link>
              <Link className={isActive("/workspace/okrs") ? "is-active" : undefined} aria-current={isActive("/workspace/okrs") ? "page" : undefined} href="/workspace/okrs"><span aria-hidden="true">02</span><span className="nav-label">{t("nav.okrs")}</span></Link>
              <Link className={isActive("/workspace/opportunities") ? "is-active" : undefined} aria-current={isActive("/workspace/opportunities") ? "page" : undefined} href="/workspace/opportunities"><span aria-hidden="true">03</span><span className="nav-label">{t("workspace.opportunityTitle")}</span></Link>
              <Link className={isActive("/workspace/initiatives") ? "is-active" : undefined} aria-current={isActive("/workspace/initiatives") ? "page" : undefined} href="/workspace/initiatives"><span aria-hidden="true">04</span><span className="nav-label">{t("workspace.initiativeTitle")}</span></Link>
              <Link className={isActive("/proposals") || pathname.startsWith("/initiatives/") ? "is-active" : undefined} aria-current={isActive("/proposals") || pathname.startsWith("/initiatives/") ? "page" : undefined} href="/proposals"><span aria-hidden="true">05</span><span className="nav-label">{t("nav.proposals")}</span></Link>
            </div>
          </div>
          <Link className={isActive(navItems[1].href) ? "is-active" : undefined} aria-current={isActive(navItems[1].href) ? "page" : undefined} href={navItems[1].href}><span aria-hidden="true">{navItems[1].icon}</span><span className="nav-label">{t(navItems[1].label)}</span></Link>
        </nav>
        <div className="sidebar-footer"><span className="eyebrow">{t("shell.currentMode")}</span><strong>{session ? session.username : t("shell.guest")}</strong><p>{t("shell.contextNote")}</p>{session ? <button className="text-link" type="button" onClick={logout}>{t("shell.signOut")} →</button> : <Link className="text-link" href="/login">{t("shell.signIn")} →</Link>}</div>
      </aside>
      <main className="main-content">
        <header className="topbar"><div><span className="breadcrumb">{t("shell.breadcrumb")}</span><strong>{session?.tenantId ?? t("shell.workspaceName")}</strong></div><div className="topbar-actions"><span className="language-label">{t("language.portuguese")}</span><span className="system-status"><i /> {t("shell.operational")}</span><button className="avatar" type="button" aria-label={t("shell.signIn")} onClick={() => router.push(session ? "/" : "/login")}>{session ? session.username.slice(0, 2).toUpperCase() : "→"}</button></div></header>
        <div className="page-content">{children}</div>
      </main>
    </div>
  );
}
