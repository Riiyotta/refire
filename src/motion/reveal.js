import { useEffect, useRef } from 'react'
import gsap from './gsap.js'
import { play, preset } from './anims.js'

/**
 * Reveal triggers (original `InView`, _app module 1126 + percents fn 3654.dU):
 *   startClear = 1 - elementTop / viewportHeight
 *   fires once when inView && clamp(startClear, 0, 1) >= threshold
 * inView = element box within the viewport grown by max(20% of vh, 200px)
 * (3654.Uf). Every reveal is also gated by the page being visible (preloader
 * gone). The state change is applied after a .01s delayedCall, as in source.
 */
export function inViewBox(rect, vw, vh) {
  const mx = Math.max(0.2 * vw, 200)
  const my = Math.max(0.2 * vh, 200)
  return rect.top <= vh + my && rect.bottom >= -my && rect.left <= vw + mx && rect.right >= -mx
}
export const startClear = (rect, vh) => Math.min(Math.max(1 - rect.top / vh, 0), 1)

// Which element the original measures for each group (the `aS` scroll
// wrapper it sits in). Text+Image uses the whole section wrapper.
const TRIGGER = {
  'text-image': (el) => el.closest('section') || el,
}

const DEFAULT_THRESHOLD = 0.1

/** Members of a group = [data-anim] descendants whose nearest group is this one. */
function members(group) {
  return [...group.querySelectorAll('[data-anim]')].filter(
    (el) => el.closest('[data-anim-group]') === group && !el.dataset.animManual,
  )
}

/**
 * Wires all [data-anim-group] reveals inside the document.
 *  - hero: plays when the page becomes visible
 *  - accordion-row: its first line plays on mount (source: <Line isVisible />)
 *  - everything else: scroll threshold (data-anim-threshold, default .1)
 */
export function useReveals(isVisible) {
  const state = useRef({ groups: [], ready: false })

  // Mount: pre-set every "from" state.
  useEffect(() => {
    const groups = [...document.querySelectorAll('[data-anim-group]')]
      .filter((g) => g.dataset.animGroup !== 'ticker')
      .map((g) => {
        const name = g.dataset.animGroup
        const els = members(g)
        let mountPlay = []
        if (name === 'accordion-row') {
          const first = els.find((e) => e.dataset.anim === 'line')
          if (first) mountPlay = [first]
        }
        els.forEach(preset)
        mountPlay.forEach((e) => play(e))
        return {
          el: g,
          name,
          trigger: (TRIGGER[name] || ((x) => x))(g),
          threshold: Number(g.dataset.animThreshold ?? DEFAULT_THRESHOLD),
          els: els.filter((e) => !mountPlay.includes(e)),
          done: false,
        }
      })
    // WebGL picture entrance (source: InView contextOnly threshold .7 around
    // ShaderPicture → animateIn: uniforms.progress → 1, 1s circ.out,
    // overwrite auto). Progress starts at 0.
    document.querySelectorAll('[data-anim="shader-reveal"]').forEach((el) => {
      el.shaderApi?.setProgress(0)
      groups.push({
        el,
        name: 'shader-reveal',
        trigger: el,
        threshold: Number(el.dataset.animThreshold ?? 0.7),
        els: [],
        run: () => {
          const api = el.shaderApi
          if (!api) return
          gsap.to(api.uniforms.progress, {
            value: 1, duration: 1, ease: 'circ.out', overwrite: 'auto', onUpdate: api.render,
          })
        },
        done: false,
      })
    })
    state.current.groups = groups
    return () => {
      groups.forEach((g) => gsap.killTweensOf(g.els))
    }
  }, [])

  useEffect(() => {
    if (!isVisible) return
    const s = state.current
    const fire = (g) => {
      g.done = true
      gsap.delayedCall(0.01, () => (g.run ? g.run() : g.els.forEach((e) => play(e))))
    }
    // Hero (and any other group flagged on-visible) reveals as soon as the page is visible.
    s.groups.filter((g) => g.name === 'hero').forEach((g) => {
      g.done = true
      // re-query: CursorInfo mounts after the first effect pass
      members(g.el).forEach((e) => play(e))
    })
    const check = () => {
      const vh = window.innerHeight
      const vw = window.innerWidth
      let pending = 0
      for (const g of s.groups) {
        if (g.done) continue
        pending++
        const r = g.trigger.getBoundingClientRect()
        if (inViewBox(r, vw, vh) && startClear(r, vh) >= g.threshold) fire(g)
      }
      if (!pending) gsap.ticker.remove(check)
    }
    gsap.ticker.add(check)
    check()
    return () => gsap.ticker.remove(check)
  }, [isVisible])
}
