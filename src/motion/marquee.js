import gsap from './gsap.js'
import { inViewBox, startClear } from './reveal.js'

/**
 * Port of the original TickerSection engine (index bundle `Ue`, speed .6):
 * per GSAP tick
 *   e = 1 - 0.9^deltaRatio
 *   delta -= autoSpeed; delta *= .5; target += delta     (steady state: -0.6px/tick)
 *   autoSpeed = lerp(autoSpeed, nextSpeed, .5e)
 *   current   = lerp(current, target, .5e)
 *   each item: x = wrap(item.x + current, railW, item.w); matrix3d translateX(x - item.x)
 * Swipe (react-swipeable, trackMouse, preventScrollOnSwipe, delta 10px):
 *   start: autoSpeed = 0, links/buttons pointer-events none
 *   move:  delta += 2 * (dX + dY) since last move
 *   end:   autoSpeed = speed, pointer-events restored
 * Runs only while the section is in view (InView threshold .1, withReset).
 */
const lerp = (a, b, t) => a + (b - a) * t
// original 3654.Q4
const wrap = (v, size, min) => (size === min ? v : ((v % size) + size + min) % size - min)
const setX = (el, x) => {
  el.style.transform = `matrix3d(1,0,0.00,0,0.00,1,0.00,0,0,0,1,0,${x},0,0,1)`
}

export function createMarquee({ ticker, rail, section, speed = 0.6, threshold = 0.1, swipeDelta = 10 }) {
  const s = {
    delta: 0, prev: [0, 0], railW: 0, viewW: 0, autoSpeed: speed, nextSpeed: speed,
    current: 0, target: 0, children: [], running: false,
  }

  const measure = () => {
    s.railW = rail.getBoundingClientRect().width
    s.viewW = window.innerWidth
    s.children = [...rail.children].map((el) => {
      setX(el, 0)
      return { el, visible: true, box: el.getBoundingClientRect() }
    })
    s.children.forEach((c) => setX(c.el, wrap(c.box.x + s.current, s.railW, c.box.width) - c.box.x))
  }

  const tick = () => {
    if (s.railW <= s.viewW) return
    const e = 1 - Math.pow(0.9, gsap.ticker.deltaRatio())
    s.delta -= s.autoSpeed
    s.delta *= 0.5
    s.target += s.delta
    s.autoSpeed = lerp(s.autoSpeed, s.nextSpeed, 0.5 * e)
    s.current = lerp(s.current, s.target, 0.5 * e)
    s.children.forEach((c) => {
      const x = wrap(c.box.x + s.current, s.railW, c.box.width)
      if (c.visible) setX(c.el, x - c.box.x)
      c.visible = x + 2 * c.box.width > 0 && x < s.viewW
    })
  }

  const start = () => {
    if (s.running) return
    s.running = true
    gsap.ticker.add(tick)
  }
  const stop = () => {
    if (!s.running) return
    s.running = false
    s.target = s.current
    gsap.ticker.remove(tick)
  }

  // In-view gate, evaluated every frame like the source's scroll update.
  const gate = () => {
    const r = section.getBoundingClientRect()
    const on = inViewBox(r, window.innerWidth, window.innerHeight) && startClear(r, window.innerHeight) >= threshold
    on ? start() : stop()
  }

  // --- swipe ---
  let down = null
  let swiping = false
  const links = () => ticker.querySelectorAll('a, button')
  const onStart = (x, y) => {
    down = [x, y]
    swiping = false
  }
  const onMove = (x, y, ev) => {
    if (!down) return
    const dx = x - down[0]
    const dy = y - down[1]
    if (!swiping) {
      if (Math.abs(dx) < swipeDelta && Math.abs(dy) < swipeDelta) return
      swiping = true
      s.prev = [0, 0]
      s.autoSpeed = 0
      const l = links()
      if (l.length) gsap.set(l, { pointerEvents: 'none' })
    }
    if (ev && ev.cancelable) ev.preventDefault()
    const ix = dx - s.prev[0]
    const iy = dy - s.prev[1]
    s.prev = [dx, dy]
    s.delta += 2 * (ix + iy)
  }
  const onEnd = () => {
    if (swiping) {
      s.autoSpeed = speed
      const l = links()
      if (l.length) gsap.set(l, { pointerEvents: '' })
    }
    down = null
    swiping = false
  }
  const md = (e) => {
    if (e.button !== 0) return
    onStart(e.clientX, e.clientY)
    document.addEventListener('mousemove', mm)
    document.addEventListener('mouseup', mu)
  }
  const mm = (e) => onMove(e.clientX, e.clientY, null)
  const mu = () => {
    document.removeEventListener('mousemove', mm)
    document.removeEventListener('mouseup', mu)
    onEnd()
  }
  const ts = (e) => onStart(e.touches[0].clientX, e.touches[0].clientY)
  const tm = (e) => onMove(e.touches[0].clientX, e.touches[0].clientY, e)
  const te = () => onEnd()
  ticker.addEventListener('mousedown', md)
  ticker.addEventListener('touchstart', ts, { passive: true })
  ticker.addEventListener('touchmove', tm, { passive: false })
  ticker.addEventListener('touchend', te)
  ticker.addEventListener('touchcancel', te)
  // native image/text drag would swallow the mouse swipe
  const noDrag = (e) => e.preventDefault()
  ticker.addEventListener('dragstart', noDrag)

  requestAnimationFrame(measure)
  // webfont swap changes item widths after the first measure
  document.fonts?.ready.then(() => measure())
  window.addEventListener('resize', measure)
  gsap.ticker.add(gate)

  return {
    state: s,
    measure,
    destroy() {
      stop()
      gsap.ticker.remove(gate)
      window.removeEventListener('resize', measure)
      ticker.removeEventListener('mousedown', md)
      ticker.removeEventListener('touchstart', ts)
      ticker.removeEventListener('touchmove', tm)
      ticker.removeEventListener('touchend', te)
      ticker.removeEventListener('touchcancel', te)
      ticker.removeEventListener('dragstart', noDrag)
      mu()
    },
  }
}
