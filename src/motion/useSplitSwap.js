import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import gsap from './gsap.js'

/**
 * Char split-text label swap (source PillButton: react-transition-group
 * switch with timeout 400 around <SplitText charType duration={400}>).
 * Measured on the original: the old label leaves first (split "out":
 * yPercent 0 → -100, 400ms, sine.inOut, stagger .01), then after the 400ms
 * timeout the new label mounts and enters (yPercent 100 → 0, 400ms,
 * circ.out, stagger .01). The first label also enters on mount.
 *
 * Returns [displayedText, ref] — put `ref` on the SplitText root and key the
 * SplitText by displayedText.
 */
export function useSplitSwap(text, timeout = 0.4) {
  const [shown, setShown] = useState(text)
  const ref = useRef(null)
  const timer = useRef(null)

  // leave, then swap
  useEffect(() => {
    if (text === shown) return
    const el = ref.current
    timer.current?.kill()
    if (el) {
      gsap.fromTo(el.querySelectorAll('.split-inner'), { yPercent: 0 }, {
        yPercent: -100, duration: 0.4, ease: 'sine.inOut', stagger: 0.01, overwrite: true,
      })
    }
    timer.current = gsap.delayedCall(timeout, () => setShown(text))
    return () => timer.current?.kill()
  }, [text]) // eslint-disable-line react-hooks/exhaustive-deps

  // enter (on mount and after every swap)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    gsap.fromTo(el.querySelectorAll('.split-inner'), { yPercent: 100 }, {
      yPercent: 0, duration: 0.4, ease: 'circ.out', stagger: 0.01, overwrite: true,
    })
  }, [shown])

  return [shown, ref]
}
