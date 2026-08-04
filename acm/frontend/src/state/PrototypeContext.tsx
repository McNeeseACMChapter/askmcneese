import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usersByRole } from "../data/seed";
import type { FixtureUser, RoleId } from "../data/types";

interface PrototypeContextValue {
  user: FixtureUser;
  roleId: RoleId;
  setRoleId: (role: RoleId) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
}

const PrototypeContext = createContext<PrototypeContextValue | null>(null);

export function PrototypeProvider({ children }: { children: ReactNode }) {
  const [roleId, setRoleId] = useState<RoleId>("project_manager");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const value = useMemo(
    () => ({
      user: usersByRole[roleId],
      roleId,
      setRoleId,
      sidebarCollapsed,
      setSidebarCollapsed,
      toggleSidebar: () => setSidebarCollapsed((c) => !c),
    }),
    [roleId, sidebarCollapsed],
  );

  return (
    <PrototypeContext.Provider value={value}>{children}</PrototypeContext.Provider>
  );
}

export function usePrototype() {
  const ctx = useContext(PrototypeContext);
  if (!ctx) throw new Error("usePrototype requires PrototypeProvider");
  return ctx;
}
