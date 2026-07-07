export const THEME_STORAGE_KEY = "theme";

export type ThemePreference = "light" | "dark";

/** Read the user's saved theme from localStorage (defaults to light). */
export function getThemePreference(): ThemePreference {
  return localStorage.getItem(THEME_STORAGE_KEY) === "dark" ? "dark" : "light";
}

/** Sync the root `<html>` class with a theme preference. */
export function applyThemePreference(preference: ThemePreference): void {
  document.documentElement.classList.toggle("dark", preference === "dark");
}

/** Persist preference to localStorage and apply it to `<html>`. */
export function setThemePreference(preference: ThemePreference): void {
  localStorage.setItem(THEME_STORAGE_KEY, preference);
  applyThemePreference(preference);
}

// Apply saved preference before React mounts to avoid a flash of the wrong theme.
applyThemePreference(getThemePreference());
