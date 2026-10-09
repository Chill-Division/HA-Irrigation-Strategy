/** The app's mark: the grow day's four phases, P0 to P3, as four arcs around a drop of water, for
 * the menu's blue tile (`.brand-mark`). The integration's and the controller app's brand images
 * are pictures of it (`frontend/scripts/make-brand-images.mjs`). */
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
      <path d="M13.1 3.07A9 9 0 0 1 20.93 10.9" />
      <path d="M20.93 13.1A9 9 0 0 1 13.1 20.93" />
      <path d="M10.9 20.93A9 9 0 0 1 3.07 13.1" />
      <path d="M3.07 10.9A9 9 0 0 1 10.9 3.07" />
      <path
        d="M12 6.8c0 0-3.7 4-3.7 6.6a3.7 3.7 0 0 0 7.4 0c0-2.6-3.7-6.6-3.7-6.6z"
        fill="currentColor"
        stroke="none"
      />
    </svg>
  );
}
