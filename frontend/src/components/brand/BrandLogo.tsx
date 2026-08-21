type BrandLogoVariant =
  | "horizontal"
  | "stacked"
  | "mark"
  | "app-icon"
  | "monochrome";

interface BrandLogoProps {
  variant?: BrandLogoVariant;
  className?: string;
  alt?: string;
  decorative?: boolean;
  eager?: boolean;
}

const LOGOS: Record<
  BrandLogoVariant,
  { src: string; width: number; height: number }
> = {
  horizontal: {
    src: "/assets/brand/askmcneese-logo-horizontal.png",
    width: 1600,
    height: 328,
  },
  stacked: {
    src: "/assets/brand/askmcneese-logo-stacked.png",
    width: 1600,
    height: 700,
  },
  mark: {
    src: "/assets/brand/askmcneese-mark.png",
    width: 1024,
    height: 740,
  },
  "app-icon": {
    src: "/assets/brand/askmcneese-app-icon.png",
    width: 512,
    height: 512,
  },
  monochrome: {
    src: "/assets/brand/askmcneese-logo-monochrome.png",
    width: 1600,
    height: 270,
  },
};

/** Locked AskMcNeese artwork extracted from brand-guide artboard 03. */
export function BrandLogo({
  variant = "horizontal",
  className = "",
  alt = "AskMcNeese ACM",
  decorative = false,
  eager = false,
}: BrandLogoProps) {
  const logo = LOGOS[variant];

  return (
    <img
      src={logo.src}
      width={logo.width}
      height={logo.height}
      alt={decorative ? "" : alt}
      aria-hidden={decorative || undefined}
      className={`brandLogo brandLogo--${variant} ${className}`.trim()}
      loading={eager ? "eager" : "lazy"}
      decoding="async"
      draggable={false}
    />
  );
}
