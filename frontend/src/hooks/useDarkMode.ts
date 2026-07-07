import { useCallback, useState } from "react";
import {
  getThemePreference,
  setThemePreference,
  type ThemePreference,
} from "../theme";

/** React state mirrors localStorage; toggling updates storage and `<html class="dark">`. */
export function useDarkMode() {
  const [preference, setPreference] = useState<ThemePreference>(getThemePreference);

  const toggle = useCallback(() => {
    const next: ThemePreference = preference === "dark" ? "light" : "dark";
    setThemePreference(next);
    setPreference(next);
  }, [preference]);

  return {
    preference,
    isDark: preference === "dark",
    toggle,
  };
}
