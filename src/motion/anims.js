import gsap from './gsap.js'

/**
 * Animation table copied from the original (_app bundle, module 4129 `v`).
 * Only the "In" states are needed (every reveal fires once).
 * NB: the original's Fade passes its `ease` prop (default "circ.inOut") over
 * the table ease, so the table ease is only used by Split (default "circ.out").
 */
export const ANIMS = {
  fade: { start: { opacity: 0 }, end: { opacity: 1 } },
  fadeBlur: {
    start: { opacity: 0, yPercent: 15, filter: 'blur(20px)' },
    end: { opacity: 1, yPercent: 0, filter: 'blur(0px)' },
  },
  fadeLeft: { start: { opacity: 0, xPercent: -20 }, end: { opacity: 1, xPercent: 0 } },
  fadeUp: { start: { opacity: 0, yPercent: 100 }, end: { opacity: 1, yPercent: 0 } },
  line: { start: { scaleX: 0 }, end: { scaleX: 1 } },
  split: { start: { yPercent: 100 }, end: { yPercent: 0 } },
  splitFade: { start: { opacity: 0 }, end: { opacity: 1 } },
}

const SPLIT_TYPES = new Set(['split', 'splitFade'])

/** Defaults per primitive (Fade: 700ms circ.inOut; Split: 800ms circ.out stagger .01; Line: 1000ms easeDecorLine). */
function defaults(type) {
  if (SPLIT_TYPES.has(type)) return { duration: 800, ease: 'circ.out', stagger: 0.01 }
  if (type === 'line') return { duration: 1000, ease: 'easeDecorLine' }
  return { duration: 700, ease: 'circ.inOut' }
}

const num = (v) => (v === undefined || v === null || v === '' ? undefined : Number(v))

/** Read data-anim-* params of an element (delay/duration in ms, stagger in s). */
export function readParams(el) {
  const type = el.dataset.anim
  const d = defaults(type)
  return {
    type,
    delay: (num(el.dataset.animDelay) ?? 0) / 1000,
    duration: (num(el.dataset.animDuration) ?? d.duration) / 1000,
    ease: el.dataset.animEase || d.ease,
    stagger: num(el.dataset.animStagger) ?? d.stagger,
  }
}

export const isSplit = (el) => SPLIT_TYPES.has(el.dataset.anim)
const inners = (el) => el.querySelectorAll('.split-inner')

/** Put an element in its pre-reveal "from" state (original: gsap.to(start, {duration:.01})). */
export function preset(el) {
  const { type } = readParams(el)
  const a = ANIMS[type]
  if (!a) return
  if (isSplit(el)) {
    el.style.opacity = 0
    el.style.pointerEvents = 'none'
    gsap.set(inners(el), a.start)
  } else {
    gsap.set(el, a.start)
  }
}

/** Play the "in" animation (gsap.fromTo, overwrite true, like the original Fade/Split). */
export function play(el, overrides = {}) {
  const p = { ...readParams(el), ...overrides }
  const a = ANIMS[p.type]
  if (!a) return null
  if (isSplit(el)) {
    el.style.opacity = ''
    el.style.pointerEvents = ''
    return gsap.fromTo(inners(el), { ...a.start }, {
      ...a.end, duration: p.duration, delay: p.delay, ease: p.ease, stagger: p.stagger,
      overwrite: true, pointerEvents: '',
    })
  }
  return gsap.fromTo(el, { ...a.start }, {
    ...a.end, duration: p.duration, delay: p.delay, ease: p.ease, overwrite: true, pointerEvents: '',
  })
}
