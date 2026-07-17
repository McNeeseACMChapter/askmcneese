import type { HTMLAttributes, ReactNode } from "react";

type GlassLevel = "navigation" | "content" | "interactive";

interface GlassSurfaceProps extends HTMLAttributes<HTMLDivElement> {
  level?: GlassLevel;
  children: ReactNode;
  as?: "div" | "aside" | "nav" | "header" | "section" | "article";
}

const levelClass: Record<GlassLevel, string> = {
  navigation: "glass-navigation",
  content: "glass-content",
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
