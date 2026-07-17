import { useCallback, useState } from "react";

const STORAGE_KEY = "askmcneese_sidebar_collapsed";

function readStoredCollapsed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function writeStoredCollapsed(collapsed: boolean) {
  try {
    localStorage.setItem(STORAGE_KEY, String(collapsed));
  } catch {
    /* ignore quota / private mode */
  }
}

export function useSidebarPrefs() {
  const [sidebarCollapsed, setCollapsed] = useState(readStoredCollapsed);

  const setSidebarCollapsed = useCallback((collapsed: boolean) => {
    setCollapsed(collapsed);
    writeStoredCollapsed(collapsed);
  }, []);

  const toggleSidebarCollapsed = useCallback(() => {
    setCollapsed((previous) => {
      const next = !previous;
      writeStoredCollapsed(next);
      return next;
    });
  }, []);

  return { sidebarCollapsed, setSidebarCollapsed, toggleSidebarCollapsed };
}
