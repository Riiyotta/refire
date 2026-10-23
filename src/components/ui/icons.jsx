// Inline SVGs — verbatim from CLONE_SPEC.md §6, converted to JSX attribute
// casing. Only deviation: pill-outline's stroke="#FEFEFE" is applied through
// the `.pill-outline` class (stroke: theme(colors.primary)) to keep hex out of JSX.

export function LogoRefire(props) {
  return (
    <svg viewBox="0 0 159 23" xmlns="http://www.w3.org/2000/svg" fill="currentColor" {...props}>
      <path d="M55.6553 0H29.1011V4.72299H55.6553V0Z" />
      <path d="M35.2769 13.7035V17.9553H55.6553V22.6839H29.1011V8.98047H55.6553V13.7035H35.2769Z" />
      <path d="M26.5767 22.6839H18.892L9.91156 13.7035H6.17018V22.6839H0V8.98047H12.8732L26.5767 22.6839Z" />
      <path d="M87.0335 8.98047V13.7035H66.6607V22.6839H60.4849V8.98047H87.0335Z" />
      <path d="M87.0335 0H60.4849V4.72299H87.0335V0Z" />
      <path d="M98.0833 8.98047H91.9131V22.6839H98.0833V8.98047Z" />
      <path d="M159 0H132.452V4.72299H159V0Z" />
      <path d="M138.622 13.7035V17.9553H159V22.6839H132.452V8.98047H159V13.7035H138.622Z" />
      <path d="M24.692 7.22497L21.1918 10.7252L15.1899 4.72324H0V0.00585938H17.4728L24.692 7.22497Z" />
      <path d="M130.163 22.6839H122.478L113.497 13.7035H109.756V22.6839H103.586V8.98047H116.459L130.163 22.6839Z" />
      <path d="M128.278 7.22497L124.778 10.7252L118.776 4.72324H91.9131V0.00585938H121.059L128.278 7.22497Z" />
    </svg>
  )
}

export function PillOutline({ className = '', ...props }) {
  return (
    <svg viewBox="0 0 116 39" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} {...props}>
      <path d="M19.5 0.5H96.5C106.993 0.5 115.5 9.00659 115.5 19.5C115.5 29.9934 106.993 38.5 96.5 38.5H19.5C9.00659 38.5 0.5 29.9934 0.5 19.5C0.5 9.00659 9.00659 0.5 19.5 0.5Z" />
    </svg>
  )
}

export function ArrowRightLong(props) {
  return (
    <svg viewBox="0 0 62 52" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M29.5022 47.6948L34.0415 51.8852L61.9258 26.1437L34.0415 0.402134L29.5022 4.59261L49.6048 23.1505L0.969421 23.1505L0.96942 29.1369L49.6048 29.1369L29.5022 47.6948Z"
        fill="currentColor"
      />
    </svg>
  )
}

export function ChevronRightThin(props) {
  return (
    <svg viewBox="0 0 10 16" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M2 14L8 8L2 2" strokeWidth="1.66667" strokeLinecap="square" />
    </svg>
  )
}

export function ChevronRightBold({ pathRef, ...props }) {
  return (
    <svg viewBox="0 0 10 16" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path ref={pathRef} d="M2 13.9778L8 7.98887L2 1.99996" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
    </svg>
  )
}

export function DoubleCircle(props) {
  return (
    <svg viewBox="0 0 80 46" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <circle cx="23" cy="23" r="22.5" stroke="currentColor" />
      <circle cx="57" cy="23" r="22.5" stroke="currentColor" strokeDasharray="1 1" />
    </svg>
  )
}

export function AccordionPlus(props) {
  return (
    <svg viewBox="0 0 39 39" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <circle cx="19.5" cy="19.5" r="19" opacity="0.3" stroke="currentColor" fill="none" />
      <circle className="circle-border" cx="19.5" cy="19.5" r="19" stroke="currentColor" fill="none" />
      <line x1="27" y1="19.5" x2="12" y2="19.5" stroke="currentColor" />
      <line x1="19.5" y1="12" x2="19.5" y2="27" stroke="currentColor" />
    </svg>
  )
}

export function ArrowUp(props) {
  return (
    <svg viewBox="0 0 12 14" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M10.2464 7.01158L11.1543 6.02996L5.57739 -1.21887e-06L0.000488871 6.02996L0.908355 7.01158L4.92892 2.6644L4.92891 13.1818L6.22587 13.1818L6.22587 2.6644L10.2464 7.01158Z"
        fill="currentColor"
      />
    </svg>
  )
}

export function ChevronDown(props) {
  return (
    <svg width="16" height="10" viewBox="0 0 16 10" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M2 2L8 8L14 2" stroke="currentColor" strokeWidth="1.66667" strokeLinecap="square" />
    </svg>
  )
}
