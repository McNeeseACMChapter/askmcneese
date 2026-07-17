import type { LucideIcon } from "lucide-react";
import { forwardRef } from "react";

interface AppIconProps {
  icon: LucideIcon;
  size?: number;
  strokeWidth?: number;
  className?: string;
  "aria-hidden"?: boolean | "true" | "false";
  title?: string;
}

/**
 * Normalized Lucide icon surface. Primary icon family for AskMcNeese.
 * Do not mix Heroicons / Font Awesome / Material here.
 */
export const AppIcon = forwardRef<SVGSVGElement, AppIconProps>(function AppIcon(
  {
    icon: Icon,
    size = 20,
    strokeWidth = 1.75,
    className = "",
    "aria-hidden": ariaHidden = true,
    title,
  },
  ref,
) {
  return (
    <Icon
      ref={ref}
      size={size}
      strokeWidth={strokeWidth}
      className={className}
      aria-hidden={ariaHidden === false || ariaHidden === "false" ? undefined : true}
      absoluteStrokeWidth
    >
      {title ? <title>{title}</title> : null}
    </Icon>
  );
});
