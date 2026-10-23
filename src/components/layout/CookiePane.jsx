import { useEffect, useRef, useState } from 'react'
import gsap from '../../motion/gsap.js'
import { cookie as copy } from '../../data/site.js'

/**
 * First-visit cookie pane (spec §2.5). Hidden once the `accept=true` cookie
 * exists; Close sets it for 1 day. Source wraps it in Fade (700ms,
 * circ.inOut both ways): fades in on mount, fades out (pointer-events none)
 * on Close and stays mounted.
 * Props: none.
 */
export default function CookiePane() {
  const [mounted, setMounted] = useState(false)
  const [visible, setVisible] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const show = !document.cookie.split('; ').includes('accept=true')
    setMounted(show)
    setVisible(show)
  }, [])

  useEffect(() => {
    if (!ref.current) return
    gsap.fromTo(
      ref.current,
      { opacity: visible ? 0 : 1 },
      { opacity: visible ? 1 : 0, duration: 0.7, ease: 'circ.inOut', overwrite: true, pointerEvents: visible ? '' : 'none' },
    )
  }, [visible, mounted])

  const close = () => {
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toUTCString()
    document.cookie = `accept=true; expires=${expires}; path=/`
    setVisible(false)
  }

  if (!mounted) return null
  return (
    <div
      ref={ref}
      style={{ opacity: 0 }}
      className="fixed bottom-0 right-0 z-99 flex w-f430 items-start justify-between bg-primary p-f26 text-f16 leading-f24 text-dark mobile:w-full mobile:p-f18 mobile:text-fmin12 mobile:leading-fmin-14-14"
      data-anim="cookie-pane"
    >
      <div className="w-f276 flex-none">{copy.title}</div>
      <div className="ml-f42 mobile:ml-f10">
        <button
          type="button"
          onClick={close}
          className="dot-link relative pl-f9 text-most-light-grey transition-colors duration-300 ease-[ease] hov:text-dark"
        >
          {copy.close}
        </button>
      </div>
    </div>
  )
}
