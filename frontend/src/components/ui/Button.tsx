import { forwardRef } from "react";
import { motion } from "framer-motion";
import { buttonHover, buttonTap } from "../../lib/motion";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md" | "lg";

interface ButtonProps {
  variant?: Variant;
  size?: Size;
  icon?: React.ReactNode;
  iconOnly?: boolean;
  children?: React.ReactNode;
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
  onClick?: () => void;
  "aria-label"?: string;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-mcneese-blue text-white hover:bg-mcneese-dark focus:ring-mcneese-blue/40",
  secondary:
    "bg-surface border border-border text-text-primary hover:bg-gray-50 focus:ring-mcneese-blue/30",
  ghost:
    "bg-transparent text-text-secondary hover:bg-gray-100 hover:text-text-primary focus:ring-gray-300/50",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs gap-1.5",
  md: "px-4 py-2 text-sm gap-2",
  lg: "px-5 py-2.5 text-base gap-2",
};

const iconOnlyClasses: Record<Size, string> = {
  sm: "p-1.5",
  md: "p-2",
  lg: "p-2.5",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", icon, iconOnly, children, className = "", disabled, type = "button", onClick, "aria-label": ariaLabel }, ref) => {
    const baseClasses =
      "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";
    
    const sizeClass = iconOnly ? iconOnlyClasses[size] : sizeClasses[size];
    
    return (
      <motion.button
        ref={ref}
        type={type}
        onClick={onClick}
        whileHover={disabled ? undefined : buttonHover}
        whileTap={disabled ? undefined : buttonTap}
        className={`${baseClasses} ${variantClasses[variant]} ${sizeClass} ${className}`}
        disabled={disabled}
        aria-label={ariaLabel}
      >
        {icon && <span className="flex-shrink-0">{icon}</span>}
        {!iconOnly && children}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
