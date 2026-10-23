import { useEffect, useRef, useState } from 'react'
import gsap from '../../motion/gsap.js'

/**
 * Custom cursor (spec §2.4), non-touch devices only (hover: hover).
 * Motion = source CustomCursor class (_app 6260 `F`, instantiated with amt .12):
 *  - starts at the window centre; every GSAP tick lerps 0.12 toward the mouse
 *    (not frame-normalised), skipped when closer than .01px, rounded to 3dp
 *  - mousedown/up: --mD → .2 / 0 over .4s (default ease), overwrite auto
 *  - document mouseout to nothing/HTML: opacity 0 (.3s power2.out); next
 *    mousemove fades back to 1
 * Native cursor stays visible. Props: none.
 */
export default function Cursor() {
  const ref = useRef(null)
  const [enabled, setEnabled] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(hover: hover)')
    const update = () => setEnabled(mq.matches)
    update()
    mq.addEventListener('change', update)
    return () => mq.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!enabled) return
    const el = ref.current
    const inner = el.querySelector('.cursor-inner')
    const amt = 0.12
    const cur = { x: window.innerWidth / 2, y: window.innerHeight / 2 }
    let fin = { ...cur }
    let visible = true
    const round = (v) => Math.round(v * 1000) / 1000
    gsap.set(inner, { '--mD': 0 })
    const setVisible = (v) => {
      gsap.to(el, { duration: 0.3, opacity: v ? 1 : 0, ease: 'power2.out' })
      visible = v
    }
    const render = () => {
      const dx = fin.x - cur.x
      const dy = fin.y - cur.y
      if (Math.sqrt(dx * dx + dy * dy) < 0.01) return
      cur.x += dx * amt
      cur.y += dy * amt
      el.style.transform = `translate3d(${round(cur.x)}px, ${round(cur.y)}px, 0)`
    }
    const onMove = (e) => {
      fin = { x: e.clientX, y: e.clientY }
      if (!visible) setVisible(true)
    }
    const press = (down) => gsap.to(inner, { duration: 0.4, '--mD': down ? 0.2 : 0, overwrite: 'auto' })
    const onDown = () => press(true)
    const onUp = () => press(false)
    const onOut = (e) => {
      const t = e.relatedTarget || e.toElement
      if (visible && !(t && t.nodeName !== 'HTML')) setVisible(false)
    }
    gsap.ticker.add(render)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mousedown', onDown)
    window.addEventListener('mouseup', onUp)
    document.addEventListener('mouseout', onOut)
    return () => {
      gsap.ticker.remove(render)
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mousedown', onDown)
      window.removeEventListener('mouseup', onUp)
      document.removeEventListener('mouseout', onOut)
    }
  }, [enabled])

  if (!enabled) return null
  return (
    <div
      ref={ref}
      className="pointer-events-none fixed left-0 top-0 z-103 [transform:translate3d(50vw,50vh,0)]"
      data-anim="cursor"
      aria-hidden="true"
    >
      <div className="cursor-inner h-[74px] w-[74px]">
        <div className="cursor-circle pointer-events-none h-full w-full rounded-full bg-cursor-circle backdrop-blur-[10px]" />
      </div>
    </div>
  )
}
