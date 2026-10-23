import { useEffect, useState } from 'react'
import { useSite } from '../../context/SiteContext.jsx'
import { header as copy } from '../../data/site.js'
import { LogoRefire, PillOutline } from '../ui/icons.jsx'
import SplitText from '../ui/SplitText.jsx'
import { useSplitSwap } from '../../motion/useSplitSwap.js'

const timeFormat = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
  timeZone: 'Atlantic/Reykjavik',
  timeZoneName: 'short',
})
const formatTime = () => timeFormat.format(new Date()).split(',')[0]

/** Live GMT clock (spec §2.2). Placeholder before mount, updates every 1s. */
export function Clock({ className = '' }) {
  const [time, setTime] = useState('weekday, date time GMT')
  useEffect(() => {
    setTime(formatTime())
    const id = setInterval(() => setTime(formatTime()), 1000)
    return () => clearInterval(id)
  }, [])
  return <span className={className}>{time}</span>
}

/**
 * Fixed header (spec §2.2): logo (closes the Contact overlay), live GMT
 * clock, Contact/Close pill. Never hides on scroll.
 * Props: none — reads/writes contact state from SiteContext.
 */
export default function Header() {
  const { contactOpen, setContactOpen } = useSite()
  const [label, labelRef] = useSplitSwap(contactOpen ? copy.close : copy.contact)
  return (
    <header className="pointer-events-none fixed top-0 z-99 w-full py-f30 text-primary mix-blend-difference [backface-visibility:hidden] [transform:translateZ(0)] tablet:py-f20 mobile:py-f18">
      <div className="flex items-center px-gap">
        <button
          type="button"
          aria-label="Refire"
          onClick={() => setContactOpen(false)}
          className="pointer-events-auto block h-f23 w-f159 mobile:h-f15 mobile:w-f104"
        >
          <LogoRefire />
        </button>
        <div className="ml-auto flex flex-wrap items-center">
          <Clock className="relative text-f16 uppercase leading-f20 mobile:text-fmin12 mobile:leading-none" />
          <button
            type="button"
            onClick={() => setContactOpen((o) => !o)}
            className="pill pointer-events-auto relative ml-f42 w-f116 rounded-f150 pb-f10 pl-f20 pr-f22 pt-f14 text-center text-f16 uppercase leading-none tablet:ml-f38 mobile:ml-f20 mobile:w-f78 mobile:px-f10 mobile:pb-f6 mobile:pt-f9 mobile:text-f12"
          >
            <PillOutline className="pill-outline absolute left-0 top-0 h-full w-full" />
            {/* char split-text label (spec §2.2), out-in swap in src/motion/useSplitSwap.js */}
            <SplitText
              as="span"
              key={label}
              ref={labelRef}
              type="chars"
              anim="split-swap"
              text={label}
              className="relative"
            />
          </button>
        </div>
      </div>
    </header>
  )
}
