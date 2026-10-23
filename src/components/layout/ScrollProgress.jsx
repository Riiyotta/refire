import { useRef } from 'react'
import { useSite } from '../../context/SiteContext.jsx'
import { useScrollProgress } from '../../motion/scroll.js'

/**
 * Page progress bar (spec §2.3). --p (0–100) is set every scroll frame
 * (src/motion/scroll.js). Props: none.
 */
export default function ScrollProgress() {
  const { lenis } = useSite()
  const ref = useRef(null)
  useScrollProgress(ref, lenis)
  return (
    <div
      ref={ref}
      className="fixed left-0 top-0 z-99 h-[2px] w-full bg-progress-track mix-blend-difference"
      style={{ '--p': 0 }}
      data-anim="scroll-progress"
    >
      <div className="page-progress-inner absolute left-0 top-0 h-full w-full bg-primary" />
    </div>
  )
}
