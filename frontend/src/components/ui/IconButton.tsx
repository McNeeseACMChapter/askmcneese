import type { ButtonHTMLAttributes, ReactNode } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  tooltip?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
}

const sizes = {
  sm: "h-10 w-10",
  md: "h-11 w-11",
  lg: "h-12 w-12",
};

export function IconButton({
  label,
  tooltip,
  children,
  size = "md",
  className = "",
  ...props
}: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={tooltip ?? label}
      className={`inline-flex ${sizes[size]} items-center justify-center rounded-xl text-text-secondary transition duration-fast hover:bg-surface-hover hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
