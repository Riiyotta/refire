import { useEffect } from 'react'
import gsap from './gsap.js'
import { inViewBox, startClear } from './reveal.js'

const lerp = (a, b, t) => a + (b - a) * t

/** Subscribe to every Lenis scroll frame (+ once now and on resize). */
function onScrollFrame(lenis, fn) {
  fn()
  lenis.on('scroll', fn)
  window.addEventListener('resize', fn)
  return () => {
    lenis.off('scroll', fn)
    window.removeEventListener('resize', fn)
  }
}

/**
 * Page progress bar (original PageProgress: style --p = 100 * currentScroll,
 * set on every scroll update, no tween).
 */
export function useScrollProgress(ref, lenis) {
  useEffect(() => {
    if (!lenis || !ref.current) return
    const el = ref.current
    return onScrollFrame(lenis, () => {
      el.style.setProperty('--p', 100 * (lenis.limit > 0 ? lenis.animatedScroll / lenis.limit : 0))
    })
  }, [lenis, ref])
}

/**
 * Scrolled picture (original ScrolledPictureSection, index bundle `be`):
 * on each scroll update while in view, with s = clamp(1 - sectionTop/vh, 0, 1)
 *   --scale = lerp(1, 1.1, s)    --x = 100*lerp(.98, 1, s)    --y = 10*(1 - lerp(.8, 1, s))
 * tweened with gsap.to(..., {duration .6, ease 'none', overwrite 'auto'}).
 * `sectionRef` is the measured wrapper (Home_pictureSection = our <section>),
 * `targetRef` holds the CSS vars.
 */
export function useScrolledPicture(sectionRef, targetRef, lenis) {
  useEffect(() => {
    if (!lenis || !sectionRef.current || !targetRef.current) return
    const section = sectionRef.current
    const target = targetRef.current
    return onScrollFrame(lenis, () => {
      const r = section.getBoundingClientRect()
      const vh = window.innerHeight
      if (!inViewBox(r, window.innerWidth, vh)) return
      const s = startClear(r, vh)
      gsap.to(target, {
        '--x': 100 * lerp(0.98, 1, s),
        '--y': 10 * (1 - lerp(0.8, 1, s)),
        '--scale': lerp(1, 1.1, s),
        ease: 'none',
        overwrite: 'auto',
        duration: 0.6,
      })
    })
  }, [lenis, sectionRef, targetRef])
}
