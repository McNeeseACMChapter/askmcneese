import type { HTMLAttributes, ReactNode } from "react";

/** Prefer chrome / control / content. Legacy names map to the same roles. */
type GlassLevel =
  | "chrome"
  | "control"
  | "content"
  | "navigation"
  | "interactive";

interface GlassSurfaceProps extends HTMLAttributes<HTMLDivElement> {
  level?: GlassLevel;
  children: ReactNode;
  as?: "div" | "aside" | "nav" | "header" | "section" | "article";
}

const levelClass: Record<GlassLevel, string> = {
  chrome: "glass-chrome",
  control: "glass-control",
  content: "glass-content",
  navigation: "glass-navigation",
  interactive: "glass-interactive",
};

export function GlassSurface({
  level = "content",
  children,
  className = "",
  as: Tag = "div",
  ...props
}: GlassSurfaceProps) {
  return (
    <Tag className={`${levelClass[level]} ${className}`} {...props}>
      {children}
    </Tag>
  );
}
