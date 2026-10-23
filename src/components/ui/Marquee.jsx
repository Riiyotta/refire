import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createMarquee } from '../../motion/marquee.js'

/**
 * Horizontal ticker rail (spec §3.6). Renders `text` `repeat` times in a
 * max-content flex rail, adding copies while the rail is narrower than the
 * viewport. Motion (src/motion/marquee.js, port of the source engine):
 * autoplay -0.6px/tick, swipe/drag with inertia, runs only while the
 * enclosing section is in view (threshold .1).
 *
 * Props:
 *  - text           item copy
 *  - repeat         minimum copies (default 3)
 *  - itemClassName  classes for each item (font, padding)
 *  - className      classes on the overflow-hidden ticker
 */
export default function Marquee({ text, repeat = 3, itemClassName = '', className = '' }) {
  const railRef = useRef(null)
  const tickerRef = useRef(null)
  const engineRef = useRef(null)
  const [count, setCount] = useState(repeat)

  useEffect(() => {
    const rail = railRef.current
    const ticker = tickerRef.current
    const engine = createMarquee({ ticker, rail, section: ticker.closest('section') || ticker })
    engineRef.current = engine
    return () => engine.destroy()
  }, [])

  // re-measure item boxes whenever copies are added
  useEffect(() => {
    engineRef.current?.measure()
  }, [count])

  useLayoutEffect(() => {
    const fill = () => {
      const rail = railRef.current
      if (!rail || !rail.firstElementChild) return
      const itemW = rail.firstElementChild.getBoundingClientRect().width
      if (!itemW) return
      const needed = Math.ceil(window.innerWidth / itemW)
      setCount(Math.max(repeat, needed))
    }
    fill()
    window.addEventListener('resize', fill)
    return () => window.removeEventListener('resize', fill)
  }, [repeat, text])

  return (
    <div ref={tickerRef} className={`relative overflow-hidden ${className}`}>
      <div ref={railRef} className="flex w-max" data-anim="marquee">
        {Array.from({ length: count }, (_, i) => (
          <div key={i} className={`shrink-0 select-none [backface-visibility:hidden] ${itemClassName}`} aria-hidden={i > 0}>
            {text}
          </div>
        ))}
      </div>
    </div>
  )
}
