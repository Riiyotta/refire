import { animAttrs } from './animAttrs.js'

/**
 * 1px decorative line (spec §3.2 `Line_wrap` / `Line_root`): a currentColor
 * track at 20% opacity plus a full-opacity fill bar (transform-origin left).
 * Rendered fully drawn; Animation tweens the fill scaleX 0 → 1
 * (1000ms, easeDecorLine) via data-anim="line".
 *
 * Props: className (on the wrap), delay (ms), threshold, anim (default 'line')
 */
export default function Line({ className = '', delay, threshold, anim = 'line' }) {
  return (
    <div className={`line-wrap relative h-px w-full ${className}`}>
      <span
        className="relative z-2 block h-full w-full origin-left bg-current"
        {...animAttrs({ anim, delay, threshold })}
      />
    </div>
  )
}
