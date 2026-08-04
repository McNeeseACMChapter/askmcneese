import type { HTMLAttributes, ReactNode } from "react";

type Level = "content" | "interactive" | "solid" | "approval";

interface SurfaceProps extends HTMLAttributes<HTMLDivElement> {
  level?: Level;
  children: ReactNode;
}

const map: Record<Level, string> = {
  content: "surface-content",
  interactive: "surface-interactive",
  solid: "surface-solid",
  approval: "surface-approval",
};

export function Surface({
  level = "content",
  className = "",
  children,
  ...rest
}: SurfaceProps) {
  return (
    <div className={`${map[level]} ${className}`.trim()} {...rest}>
      {children}
    </div>
  );
}
