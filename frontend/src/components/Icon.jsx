// The console's line icons, drawn rather than downloaded: one 24px grid, one
// stroke weight, `currentColor` throughout — so an icon in the sidebar takes the
// nav's ink and the same icon in a card's corner takes the card's.
//
// They are decoration in the strict sense: every one of them sits beside a text
// label that says the same thing, so each is `aria-hidden` and nothing is
// announced twice.

const PATHS = {
  // Overview — the card grid itself.
  overview: (
    <>
      <rect x="3" y="3" width="7.5" height="7.5" rx="1.5" />
      <rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5" />
      <rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5" />
      <rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5" />
    </>
  ),
  // Case file — a folder with a document in it.
  case: (
    <>
      <path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2.5h7A1.5 1.5 0 0 1 19 9v8.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 3 17.5Z" />
      <path d="M7.5 11.5h8M7.5 15h5" />
    </>
  ),
  // Deadlines — a clock.
  deadlines: (
    <>
      <circle cx="12" cy="12.5" r="8" />
      <path d="M12 8v4.5l3 2" />
    </>
  ),
  // Denials — a document with a line struck through it.
  denials: (
    <>
      <path d="M6 3.5h7L18.5 9v11.5a1 1 0 0 1-1 1h-11.5a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1Z" />
      <path d="M13 3.5V9h5.5" />
      <path d="M8.5 15.5h7" />
    </>
  ),
  // Letters — an envelope.
  letters: (
    <>
      <rect x="3" y="5.5" width="18" height="13" rx="1.5" />
      <path d="m3.8 6.6 8.2 6.2 8.2-6.2" />
    </>
  ),
  // Decisions — a question waiting on a person.
  decisions: (
    <>
      <path d="M20.5 15.5a2 2 0 0 1-2 2H8l-4.5 3.5v-14a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2Z" />
      <path d="M9.8 9.2a2.3 2.3 0 0 1 4.4.8c0 1.6-2.2 1.9-2.2 3.3" />
      <path d="M12 15.6h.01" />
    </>
  ),
  // Journal — a bound ledger.
  journal: (
    <>
      <path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v18H6.5A1.5 1.5 0 0 1 5 19.5Z" />
      <path d="M5 16.5h14" />
      <path d="M8.5 7.5h7M8.5 11h5" />
    </>
  ),
  // Autonomy — a dial.
  autonomy: (
    <>
      <path d="M4 8h10M18 8h2M4 16h4M12 16h8" />
      <circle cx="16" cy="8" r="2.2" />
      <circle cx="10" cy="16" r="2.2" />
    </>
  ),
  // Hospitals — a building with a cross.
  hospital: (
    <>
      <path d="M4.5 20.5v-14a1 1 0 0 1 1-1h13a1 1 0 0 1 1 1v14M3 20.5h18" />
      <path d="M12 8.5v5M9.5 11h5" />
      <path d="M10 20.5v-3.5h4v3.5" />
    </>
  ),
  // Safety — a shield with a tick.
  safety: (
    <>
      <path d="M12 3.5 19 6v5.5c0 4.3-2.8 7.6-7 9-4.2-1.4-7-4.7-7-9V6Z" />
      <path d="m8.8 12 2.2 2.2 4.2-4.4" />
    </>
  ),
  // Bottom-left navigation arrow on a card.
  arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
}

export default function Icon({ name, size = 22, className = '' }) {
  const path = PATHS[name]
  if (!path) return null
  return (
    <svg
      className={`icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {path}
    </svg>
  )
}

// The status strip's subject: a denial letter and a clock, and nothing else.
// No photograph and no drawing of a person — the thing on this screen is a
// piece of paper with a date on it.
export function DenialAndClock({ className = '' }) {
  return (
    <svg
      className={`strip-art ${className}`.trim()}
      viewBox="0 0 176 116"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      {/* the letter */}
      <rect x="16" y="8" width="92" height="100" rx="4"
            fill="rgba(255,255,255,.06)" stroke="rgba(255,255,255,.34)" strokeWidth="1.5" />
      <path d="M30 26h50M30 38h64M30 50h58M30 62h40"
            stroke="rgba(255,255,255,.3)" strokeWidth="2.5" strokeLinecap="round" />
      {/* the stamp across it */}
      <rect x="27" y="74" width="62" height="22" rx="3"
            fill="none" stroke="var(--brand)" strokeWidth="2" />
      <path d="M35 85h46" stroke="var(--brand)" strokeWidth="2" strokeLinecap="round" />
      {/* the clock, overlapping the corner */}
      <circle cx="128" cy="74" r="30" fill="var(--slate-2)" />
      <circle cx="128" cy="74" r="30" stroke="rgba(255,255,255,.4)" strokeWidth="1.5" />
      <path d="M128 56v18l12 8" stroke="var(--brand)" strokeWidth="3"
            strokeLinecap="round" strokeLinejoin="round" />
      <path d="M128 46.5v3M155.5 74h-3M128 101.5v-3M100.5 74h3"
            stroke="rgba(255,255,255,.5)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

// The strip's subject here: a panel comparing hospitals, one bar marked.
export function HospitalArt({ className = '' }) {
  return (
    <svg className={`strip-art ${className}`.trim()} viewBox="0 0 176 116" fill="none" aria-hidden="true" focusable="false">
      <rect x="16" y="8" width="144" height="100" rx="4" fill="rgba(255,255,255,.06)" stroke="rgba(255,255,255,.34)" strokeWidth="1.5" />
      <path d="M32 92h112" stroke="rgba(255,255,255,.3)" strokeWidth="2.5" strokeLinecap="round" />
      <rect x="38" y="52" width="16" height="40" rx="2" fill="rgba(255,255,255,.22)" />
      <rect x="66" y="34" width="16" height="58" rx="2" fill="rgba(255,255,255,.22)" />
      <rect x="94" y="62" width="16" height="30" rx="2" fill="rgba(255,255,255,.22)" />
      <rect x="122" y="44" width="16" height="48" rx="2" fill="rgba(255,255,255,.22)" />
      <rect x="61" y="27" width="26" height="72" rx="3" fill="none" stroke="var(--brand)" strokeWidth="2" />
    </svg>
  )
}
