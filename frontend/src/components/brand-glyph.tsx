/** The seedling, drawn twice: once wide in the tile's colour (`.brand-glyph-halo`), so the tank's
 * lines stop short of it and it stands in front, then over that in the glyph's own colour. */
const seedling = (
  <>
    <path d="M5 21.5c0-3 1.6-4.6 1.2-8.2" />
    <path
      d="M6.1 14.9C7.11 13.38 4.19 10.78 1.7 10.8C1.85 13.28 4.65 16.01 6.1 14.9Z"
      fill="currentColor"
    />
    <path
      d="M6.2 13.2C8.09 14.58 11.98 10.72 12.3 7.4C8.96 7.56 4.92 11.24 6.2 13.2Z"
      fill="currentColor"
    />
  </>
);

/** The app's mark: a tank of water with a seedling in front of it, for the menu's blue tile
 * (`.brand-mark`). The integration's and the controller app's brand images are pictures of it
 * (`frontend/scripts/make-brand-images.mjs`). */
export function BrandGlyph({ size = 23 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="9.5" y="3" width="12" height="18" rx="2.5" />
      <path d="M9.5 6.5h12" />
      <path
        d="M9.5 11.5c1.6-1 2.4-1 4 0s2.4 1 4 0 2.4-1 4 0v7a2.5 2.5 0 0 1-2.5 2.5h-7a2.5 2.5 0 0 1-2.5-2.5z"
        fill="currentColor"
        stroke="none"
        opacity={0.45}
      />
      <path d="M9.5 11.5c1.6-1 2.4-1 4 0s2.4 1 4 0 2.4-1 4 0" />
      <g className="brand-glyph-halo" strokeWidth={4.5}>
        {seedling}
      </g>
      {seedling}
    </svg>
  );
}
