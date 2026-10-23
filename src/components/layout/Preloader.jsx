import { useEffect, useRef, useState } from 'react'
import gsap from '../../motion/gsap.js'
import { preloader as copy } from '../../data/site.js'

/**
 * Full-screen preloader (spec §2.1).
 * Progress = fraction of <img> elements decoded (0 images → 1 after 300ms).
 * Motion (source _app Preloader): on each progress change `--p` and the
 * integer counter tween to it over 4s sine.inOut (overwrite auto); when the
 * counter tween completes at progress 1, the root fades out (1s, delay .2s,
 * sine.inOut) while the line+counter group goes opacity 0 / blur(20px) over
 * 2s; onComplete fires when the root fade ends. Dots blink via CSS.
 *
 * Props:
 *  - onComplete   called when loading has finished (Layout unmounts this)
 */
export default function Preloader({ onComplete }) {
  const [progress, setProgress] = useState(0)
  const [count, setCount] = useState(0)
  const [loaded, setLoaded] = useState(false)
  const rootRef = useRef(null)
  const groupRef = useRef(null)
  const counter = useRef({ x: 0, p: 0 })

  useEffect(() => {
    let cancelled = false
    let timer
    const imgs = Array.from(document.images)
    if (!imgs.length) {
      timer = setTimeout(() => !cancelled && setProgress(1), 300)
    } else {
      let done = 0
      imgs.forEach((img) => {
        const p = img.decode ? img.decode() : Promise.resolve()
        p.catch(() => {}).finally(() => {
          done += 1
          if (!cancelled) setProgress(done / imgs.length)
        })
      })
    }
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    const t1 = gsap.to(rootRef.current, { duration: 4, '--p': progress, ease: 'sine.inOut', overwrite: 'auto' })
    const t2 = gsap.to(counter.current, {
      duration: 4,
      x: 100 * progress,
      p: progress,
      overwrite: 'auto',
      roundProps: 'x',
      ease: 'sine.inOut',
      onUpdate: () => setCount(counter.current.x),
      onComplete: () => progress === 1 && setLoaded(true),
    })
    return () => {
      t1.kill()
      t2.kill()
    }
  }, [progress])

  const done = useRef(onComplete)
  done.current = onComplete
  useEffect(() => {
    if (!loaded) return
    gsap.to(rootRef.current, {
      opacity: 0,
      duration: 1,
      delay: 0.2,
      ease: 'sine.inOut',
      onComplete: () => done.current?.(),
    })
    gsap.to(groupRef.current, { opacity: 0, filter: 'blur(20px)', duration: 2 })
  }, [loaded])

  return (
    <div
      ref={rootRef}
      className="fixed left-0 top-0 z-100 h-screen w-screen bg-dark text-primary"
      style={{ '--p': 0 }}
      data-anim="preloader"
    >
      <div className="flex h-full w-full items-end">
        <div className="h-full w-full px-f30 [--offset:calc(220*var(--vw-unit))] tablet:px-f20 tablet:[--offset:calc(160*var(--vw-unit))] mobile:px-f10 mobile:[--offset:calc(100*var(--vw-unit))]">
          <div ref={groupRef} className="flex h-full flex-col justify-center" data-anim="preloader-progress-group">
            <div className="h-px w-full overflow-hidden">
              <span className="preloader-line-fill block h-full w-full bg-primary" />
            </div>
            <div className="preloader-progress relative mt-f17 text-right text-f75 font-light leading-none tablet:mt-f14 tablet:text-f60 mobile:mt-f8 mobile:text-f36">
              <span className="invisible inline-block w-[var(--offset)]">00%</span>
              <span className="preloader-numbers absolute bottom-0 right-0" data-anim="preloader-counter">
                {count}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute left-0 top-0 flex h-full w-full flex-col justify-between p-f24 text-f14 uppercase leading-none tracking-[.3em] text-grey mobile:p-f10 mobile:text-f12">
        <div className="flex justify-between">
          <span className="text-f20 mobile:text-f16">{copy.decorLeft}</span>
          <div className="flex">
            <span className="mr-f29">{copy.decorRight[0]}</span>
            <span>{copy.decorRight[1]}</span>
          </div>
        </div>
        <div className="flex justify-between">
          <span className="mobile:mx-auto">
            {copy.initializing}
            {[0.2, 0.4, 0.6].map((d) => (
              <span key={d} data-anim="preloader-dot" data-anim-delay={d * 1000}>
                .
              </span>
            ))}
          </span>
          <span className="mobile:hidden">{copy.tagline}</span>
        </div>
      </div>
    </div>
  )
}
