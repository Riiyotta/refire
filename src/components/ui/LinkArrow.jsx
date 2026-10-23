import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { DrawSVGPlugin } from 'gsap/DrawSVGPlugin'
import { ChevronRightBold } from './icons.jsx'

gsap.registerPlugin(DrawSVGPlugin)

/**
 * Underlined uppercase link with a chevron that draws on hover (spec §5 LinkArrow).
 * Rest: underline visible, chevron undrawn (DrawSVG "-0.2% -0.2%").
 * Hover: underline (origin right) scaleX 1 → 0, 0.8s power4.inOut; chevron draws
 * to "0% 100%", 0.4s sine.out, starting 0.3s before the underline ends.
 * Mouse leave reverses.
 *
 * Props: href, children, target, rel, className, ...rest (anchor attributes)
 */
export default function LinkArrow({ href, children, target, rel, className = '', ...rest }) {
  const underlineRef = useRef(null)
  const pathRef = useRef(null)
  const tlRef = useRef(null)

  useEffect(() => {
    gsap.set(pathRef.current, { drawSVG: '-0.2% -0.2%' })
    const tl = gsap
      .timeline({ paused: true })
      .fromTo(underlineRef.current, { scaleX: 1 }, { scaleX: 0, duration: 0.8, ease: 'power4.inOut' })
      .fromTo(
        pathRef.current,
        { drawSVG: '-0.2% -0.2%' },
        { drawSVG: '0% 100%', duration: 0.4, ease: 'sine.out' },
        '-=0.3',
      )
    tlRef.current = tl
    return () => tl.kill()
  }, [])

  return (
    <a
      href={href}
      target={target}
      rel={rel}
      className={`inline-flex items-center ${className}`}
      onMouseEnter={() => tlRef.current?.play()}
      onMouseLeave={() => tlRef.current?.reverse()}
      {...rest}
    >
      <span className="relative block text-f24 leading-none uppercase tablet:text-f18 mobile:text-fmin12">
        {children}
        <span
          ref={underlineRef}
          className="absolute bottom-0 left-0 block h-px w-full origin-right bg-current"
        />
      </span>
      <ChevronRightBold
        pathRef={pathRef}
        className="-mt-px ml-f14 h-f16 w-f10 fill-transparent tablet:ml-f8 tablet:h-f14 tablet:w-f8 mobile:ml-f6 mobile:h-f9 mobile:w-f6"
      />
    </a>
  )
}
