import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import Line from './Line.jsx'
import Reveal from './Reveal.jsx'
import SplitText from './SplitText.jsx'
import { AccordionPlus } from './icons.jsx'

/**
 * Single-open accordion (spec §3.7). All items start closed; clicking the
 * open item closes it. Body height animates 0 ↔ auto, GSAP .5s power1.inOut;
 * icon rotates 45deg (.3s); hover draws the icon circle.
 *
 * Props:
 *  - items      [{ title: string, body: string (HTML, set via innerHTML) }]
 *  - className  extra classes on the root
 *  - threshold  reveal threshold for each row (spec default 0.1)
 */
export default function Accordion({ items, className = '', threshold = 0.1 }) {
  const [openIndex, setOpenIndex] = useState(-1)
  return (
    <div className={className}>
      {items.map((item, i) => (
        <AccordionItem
          key={i}
          item={item}
          isOpen={openIndex === i}
          isLast={i === items.length - 1}
          threshold={threshold}
          onToggle={() => setOpenIndex((cur) => (cur === i ? -1 : i))}
        />
      ))}
    </div>
  )
}

function AccordionItem({ item, isOpen, isLast, onToggle, threshold }) {
  const bodyRef = useRef(null)
  const mounted = useRef(false)

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      return
    }
    gsap.to(bodyRef.current, {
      height: isOpen ? 'auto' : 0,
      duration: 0.5,
      ease: 'power1.inOut',
      overwrite: true,
    })
  }, [isOpen])

  return (
    <div className={`accordion-item ${isOpen ? 'is-open' : ''}`} data-anim-group="accordion-row" data-anim-threshold={threshold}>
      <Line />
      <button
        type="button"
        aria-expanded={isOpen}
        onClick={onToggle}
        className="accordion-btn flex w-full items-center py-f26 text-left tablet:justify-between tablet:py-f22"
      >
        <SplitText
          as="h5"
          text={item.title}
          stagger={0.03}
          className="flex-[2_1_0%] text-f38 leading-none tablet:text-f20 mobile:max-w-[61%] mobile:text-f16"
        />
        <Reveal as="span" className="accordion-icon block h-f39 w-f39 shrink-0 tablet:h-f29 tablet:w-f29">
          <AccordionPlus />
        </Reveal>
      </button>
      <div ref={bodyRef} className="h-0 overflow-hidden">
        <Reveal
          className="accordion-body w-f740 pb-f56 pt-f18 text-f24 leading-[1.375] text-accordion tablet:w-f395 tablet:pb-f24 tablet:pt-0 tablet:text-fmin12 mobile:w-[85%] mobile:pb-f23"
          dangerouslySetInnerHTML={{ __html: item.body }}
        />
      </div>
      {isLast && <Line />}
    </div>
  )
}
