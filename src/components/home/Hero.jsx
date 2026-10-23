import { useEffect, useRef, useState } from 'react'
import { useSite } from '../../context/SiteContext.jsx'
import Reveal from '../ui/Reveal.jsx'
import SplitText from '../ui/SplitText.jsx'
import { ArrowRightLong, ChevronRightThin } from '../ui/icons.jsx'

/** "X . n / Y . n" live pointer readout, non-touch only (spec §3.1 CursorInfo). */
function CursorInfo() {
  const [enabled, setEnabled] = useState(false)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  useEffect(() => {
    setEnabled(window.matchMedia('(hover: hover)').matches)
    const onMove = (e) => setPos({ x: Math.round(e.clientX), y: Math.round(e.clientY) })
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [])
  if (!enabled) return null
  return (
    <Reveal
      delay={500}
      className="absolute right-f20 top-f151 z-2 text-grey tablet:top-f100 mobile:right-f10 mobile:top-f80"
    >
      <div className="cursor-info relative w-fmax-90-110 pl-f17 text-fmin14 uppercase leading-[1.2] tracking-[.3em] mobile:w-fmax-80-90 mobile:text-fmin12">
        <span className="block">x . {pos.x}</span>
        <span className="block">y . {pos.y}</span>
      </div>
    </Reveal>
  )
}

/**
 * Hero (spec §3.1). Video plays only while the hero is in view and the
 * preloader has finished.
 * Props: data — { decor, scroll, subtitle, titleLines[2], centerText, link{label,href}, video{src,poster} }
 */
export default function Hero({ data }) {
  const { isVisible } = useSite()
  const rootRef = useRef(null)
  const videoRef = useRef(null)
  const [inView, setInView] = useState(true)

  useEffect(() => {
    const io = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting))
    io.observe(rootRef.current)
    return () => io.disconnect()
  }, [])

  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    if (inView && isVisible) v.play().catch(() => {})
    else v.pause()
  }, [inView, isVisible])

  return (
    <section
      ref={rootRef}
      className="relative flex h-screen flex-col justify-end bg-dark pl-gap text-primary"
      data-anim-group="hero"
    >
      <div className="absolute left-0 top-0 z-0 h-full w-full">
        <video
          ref={videoRef}
          className="absolute left-0 top-0 h-full w-full object-cover"
          src={data.video.src}
          poster={data.video.poster}
          muted
          loop
          autoPlay
          playsInline
          preload="auto"
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>

      <Reveal
        delay={500}
        className="absolute left-gap top-f151 z-2 text-f20 uppercase leading-[1.2] tablet:top-f135 mobile:top-f69 mobile:text-f16"
      >
        {data.decor}
      </Reveal>
      <Reveal
        delay={500}
        className="absolute left-gap top-f181 z-2 text-fmin14 uppercase leading-fmin-22-24 tracking-[.3em] text-dark-grey tablet:top-f166 mobile:bottom-f9 mobile:top-auto mobile:text-fmin12 mobile:leading-none mobile:mix-blend-difference"
      >
        {data.scroll}
      </Reveal>
      <CursorInfo />

      <div className="relative flex items-end mobile:flex-wrap">
        <div className="flex items-end pb-f12 tablet:w-f403 tablet:flex-col tablet:items-start mobile:mb-f42 mobile:pb-0">
          <div className="w-f765 flex-none tablet:mb-f6 tablet:w-full mobile:mb-f10">
            <Reveal
              delay={500}
              className="dot-before relative mb-f19 pl-f18 text-fmin14 uppercase leading-fmin-22-24 tracking-[.3em] text-grey tablet:pl-f11 mobile:mb-f17 mobile:pl-f6 mobile:text-fmin12 mobile:leading-[.9]"
            >
              {data.subtitle}
            </Reveal>
            <h1 className="text-f157 font-light capitalize leading-f146 tablet:text-f82 tablet:leading-[.9] mobile:text-f55">
              {/* source: .titleItem (inline-flex) > Fade span (fadeBlur) + sibling arrow (fadeLeft) */}
              <div className="inline-flex flex-wrap items-center">
                <Reveal as="span" anim="fadeBlur" delay={0} duration={1500}>
                  {data.titleLines[0]}
                </Reveal>
                <Reveal
                  as="span"
                  anim="fadeLeft"
                  delay={700}
                  className="ml-f44 mt-f14 block h-f52 w-f62 flex-none tablet:ml-f30 tablet:mt-f14 tablet:h-f32 tablet:w-f38 mobile:ml-f13 mobile:mt-f8 mobile:h-f21 mobile:w-f25"
                >
                  <ArrowRightLong />
                </Reveal>
              </div>
              <div className="inline-flex flex-wrap items-center">
                <Reveal as="span" anim="fadeBlur" delay={200} duration={1500}>
                  {data.titleLines[1]}
                </Reveal>
              </div>
            </h1>
          </div>
          <SplitText
            text={data.centerText}
            type="chars"
            anim="splitFade"
            delay={700}
            duration={3000}
            stagger={0.02}
            ease="circ.out"
            className="uppercase-first ml-f178 max-w-f263 pb-f12 text-f42 font-light leading-none tracking-[.05em] text-alt-dark-grey2 mix-blend-difference tablet:ml-0 tablet:pb-0 tablet:text-f36 tablet:leading-f42 mobile:text-f18 mobile:leading-[.95]"
          />
        </div>
        <div className="ml-auto flex items-center mobile:w-full mobile:justify-end">
          <Reveal
            as="a"
            delay={700}
            duration={1000}
            href={data.link.href}
            target="_blank"
            rel="noopener noreferrer"
            className="glass relative inline-flex items-center overflow-hidden p-f27 text-f24 capitalize leading-none tablet:px-f24 tablet:pb-f17 tablet:pt-f18 tablet:text-f18 mobile:px-f12 mobile:pb-f10 mobile:pt-f11 mobile:text-fmin12"
          >
            <span className="relative z-3">{data.link.label}</span>
            <ChevronRightThin className="relative z-3 ml-f28 h-f16 w-f10 flex-none fill-none stroke-current tablet:ml-f10 mobile:h-f9 mobile:w-f5" />
          </Reveal>
        </div>
      </div>
    </section>
  )
}
