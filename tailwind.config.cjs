// CommonJS so Tailwind can hot-reload this file in the running dev server
// (Node 20.19+ caches require()d ESM configs and never reloads them).

// Design tokens — CLONE_SPEC.md §0.3 (verbatim :root tokens) plus the literal
// colours called out in §0.3 "Used on this page" / §2.4 / §3.1 / §3.8.
// JS that cannot use classes (three.js clear colour) reads these through CSS
// custom properties emitted in src/index.css via theme().
const colors = {
  transparent: 'transparent',
  current: 'currentColor',
  primary: '#fefefe', // --primary-color
  dark: '#060508', // --dark-color
  'alt-dark': '#0e0e0e', // --alt-dark-color (key card bg)
  grey: '#c8c8c8', // --grey-color
  'alt-dark-grey2': '#8e8e8e', // --alt-dark-grey2 (hero centre text)
  'dark-grey': '#8b8b8b', // --dark-grey-color (muted labels)
  'alt-dark-grey': '#383739', // --alt-dark-grey-color (dim headings)
  'alt-grey': '#848484', // --alt-grey-color
  'darkness-grey': '#555555', // --darkness-grey-color (footer rule)
  'light-grey': 'silver', // --light-grey-color
  'light-dark': '#2a2a2a', // --light-dark-color
  'most-dark': '#383838', // --most-dark-color (submit hover bg)
  'alt-light-grey': '#3d3c3e', // --alt-light-grey-color
  'code-dark': '#4f4f4f', // --code-dark-color
  red: '#c39797', // --red-color
  gb: '#828183', // --gb-color (select borders)
  'most-light-grey': '#d0d0d0', // --most-light-grey (cookie link)
  'tr-grey': 'rgba(6,5,8,.15)', // --tr-grey-color
  accordion: '#888888', // literal #888 accordion body (§0.3)
  selection: '#a59e99', // ::selection (§0.3)
  'progress-track': 'rgba(6,5,8,.1)', // PageProgress bg (§2.3)
  glass: 'hsla(0,0%,100%,.1)', // hero link glass (§3.1)
  'cursor-circle': 'hsla(0,0%,71%,.25)', // custom cursor (§2.4)
  'webgl-clear': '#eeeeee', // three.js clearColor 0xEEEEEE (§3.8)
}

// Fluid unit F(N) = N / --gfs * 100vw (spec §0.2). --vw-unit is set per
// breakpoint in src/index.css, so `f{N}` resolves correctly at every width.
const F = (n) => `calc(${n} * var(--vw-unit))`
const range = (max) => Array.from({ length: max + 1 }, (_, i) => i)
const fluid = Object.fromEntries(range(1500).map((n) => [`f${n}`, F(n)]))
// max(12px, F(N)) clamps used for the small labels (spec §0.2 / §1).
const fmin = Object.fromEntries(range(40).map((n) => [`fmin${n}`, `max(12px, ${F(n)})`]))

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    // Desktop-first breakpoints from spec §0.2 (max-width media queries).
    // Order matters: tablet rules must come before mobile overrides.
    screens: {
      tablet: { max: '834px' },
      mobile: { max: '520px' },
    },
    colors,
    fontFamily: {
      suisse: ['SuisseIntl', 'Arial', 'Helvetica', 'sans-serif'],
    },
    extend: {
      spacing: {
        ...fluid,
        gap: 'var(--gap-content)',
      },
      fontSize: { ...fluid, ...fmin },
      lineHeight: {
        ...fluid,
        // label line-heights with their own px floors (spec §1 / source CSS)
        'fmin-22-24': `max(22px, ${F(24)})`,
        'fmin-18-20': `max(18px, ${F(20)})`,
        'fmin-14-14': `max(14px, ${F(14)})`,
        'fmin-16-16': `max(16px, ${F(16)})`,
        'fmin-14-17': `max(14px, ${F(17)})`,
      },
      borderRadius: fluid,
      maxWidth: {
        ...fluid,
        // TextImage items: calc(50% - F(15)) desktop, calc(50% - F(10)) tablet (spec §3.8)
        'half-f15': `calc(50% - ${F(15)})`,
        'half-f10': `calc(50% - ${F(10)})`,
      },
      width: { 'fmax-90-110': `max(90px, ${F(110)})`, 'fmax-80-90': `max(80px, ${F(90)})` },
      zIndex: { 2: '2', 3: '3', 89: '89', 99: '99', 100: '100', 103: '103' },
      transitionTimingFunction: {
        pill: 'cubic-bezier(.86,0,.12,1)',
        underline: 'cubic-bezier(1,0,.29,1)',
        option: 'cubic-bezier(.165,.84,.44,1)',
        submit: 'cubic-bezier(.36,.28,0,.99)',
        'decor-line': 'cubic-bezier(.075,.82,.165,1)',
        'form-hover-line': 'cubic-bezier(.215,.61,.355,1)',
      },
    },
  },
  plugins: [
    // Hover rules live under (hover:hover); :active mirrors them under
    // (hover:none) — spec §0.2.
    ({ addVariant }) => {
      addVariant('hov', ['@media (hover: hover) { &:hover }', '@media (hover: none) { &:active }'])
      addVariant('group-hov', [
        '@media (hover: hover) { :merge(.group):hover & }',
        '@media (hover: none) { :merge(.group):active & }',
      ])
    },
  ],
}
