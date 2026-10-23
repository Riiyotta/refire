import { useRef } from 'react'
import { useSite } from '../../context/SiteContext.jsx'
import { useScrolledPicture } from '../../motion/scroll.js'

/**
 * Scroll-linked picture (spec §3.5). Starts at the spec's initial vars
 * (--x 98, --y 2, --scale 1); src/motion/scroll.js drives them from scroll.
 * Props: data — { src, alt }
 */
export default function ScrolledPicture({ data }) {
  const { lenis } = useSite()
  const sectionRef = useRef(null)
  const pictureRef = useRef(null)
  useScrolledPicture(sectionRef, pictureRef, lenis)
  return (
    <section ref={sectionRef} className="-mt-px bg-dark pb-f140 pt-f156 tablet:pb-f68 tablet:pt-f78 mobile:pb-f40 mobile:pt-f48">
      <div
        ref={pictureRef}
        className="scrolled-picture relative h-screen [backface-visibility:hidden] tablet:h-[78vh] mobile:h-[68vh]"
        data-anim="scrolled-picture"
      >
        <div className="relative h-full w-full">
          <div className="scrolled-picture-clip absolute left-0 top-0 h-full w-full">
            <img
              src={data.src}
              alt={data.alt}
              className="scrolled-picture-img pointer-events-none absolute left-0 top-0 h-full w-full select-none object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
