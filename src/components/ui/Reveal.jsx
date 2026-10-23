import { animAttrs } from './animAttrs.js'

/**
 * Reveal wrapper (spec §4.1 / §4.2). Renders children in their final visible
 * state and tags the element with data-anim hooks for the Animation pass.
 *
 * Props:
 *  - as         element tag (default 'div')
 *  - anim       'fade' | 'fadeBlur' | 'fadeLeft' | 'fadeUp' | ... (default 'fade')
 *  - delay      ms
 *  - duration   ms (spec default 700)
 *  - ease       GSAP ease name (spec default circ.inOut)
 *  - threshold  0–1 trigger point (spec §4.1)
 *  - className, ...rest passed through
 */
export default function Reveal({
  as: Tag = 'div',
  anim = 'fade',
  delay,
  duration,
  ease,
  threshold,
  className = '',
  children,
  ...rest
}) {
  return (
    <Tag className={className} {...animAttrs({ anim, delay, duration, ease, threshold })} {...rest}>
      {children}
    </Tag>
  )
}
