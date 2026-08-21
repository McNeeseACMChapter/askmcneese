import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant =
  | "primary"
  | "secondary"
  | "ghost"
  | "danger"
  | "danger-outline";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
}

const map: Record<Variant, string> = {
  primary: "acm-btn acm-btn--primary",
  secondary: "acm-btn acm-btn--secondary",
  ghost: "acm-btn acm-btn--ghost",
  danger: "acm-btn acm-btn--danger",
  "danger-outline": "acm-btn acm-btn--danger-outline",
};

export function Button({
  variant = "primary",
  className = "",
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button type={type} className={`${map[variant]} ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}
