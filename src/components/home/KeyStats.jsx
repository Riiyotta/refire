import Reveal from '../ui/Reveal.jsx'
import SplitText from '../ui/SplitText.jsx'
import { ArrowRightLong, DoubleCircle } from '../ui/icons.jsx'

/**
 * Key stat card (spec §3.4 KeyCard). Each card is its own reveal group (0.3).
 * Props: label, number (int, zero-padded to 3), title, value
 */
export function KeyCard({ label, number, title, value }) {
  return (
    <div
      className="relative flex h-f745 flex-col justify-between rounded-f15 bg-alt-dark px-f38 pb-f11 pt-f35 text-primary tablet:h-f550 tablet:rounded-f14 tablet:px-f20 tablet:pb-f6 tablet:pt-f31 mobile:h-f339 mobile:pb-0 mobile:pl-f12 mobile:pr-f14 mobile:pt-f10"
      data-anim-group="key-card"
      data-anim-threshold="0.3"
    >
      <Reveal>
        <div className="flex justify-between text-f16 font-medium uppercase leading-[1.5] text-dark-grey mobile:text-fmin12">
          <span>{label}</span>
          <span>{String(number).padStart(3, '0')}</span>
        </div>
        <div className="mt-f21 h-f46 mobile:mt-f12 mobile:h-f26">
          <DoubleCircle className="max-h-full w-auto fill-transparent" />
        </div>
      </Reveal>
      <div>
        <Reveal
          delay={300}
          className="rule-after relative mb-f34 max-w-f460 pb-f14 tablet:mb-f30 tablet:pb-f11 mobile:mb-f15 mobile:max-w-[85%] mobile:pb-f11"
        >
          <span className="inline-flex items-center text-f24 capitalize leading-[1.38] text-dark-grey tablet:text-f20 mobile:text-fmin14">
            {title}
            <ArrowRightLong className="ml-f10 h-f13 w-f16 flex-none tablet:h-f12 tablet:w-f14 mobile:ml-f8 mobile:h-f9 mobile:w-f11" />
          </span>
        </Reveal>
        <SplitText
          text={value}
          delay={500}
          stagger={0.05}
          duration={800}
          className="-ml-f7 text-f188 font-extralight uppercase leading-none tablet:ml-0 tablet:text-f170 mobile:text-f100"
        />
      </div>
    </div>
  )
}

/**
 * Key stats grid (spec §3.4).
 * Props: items — [{ label, number, title, value }]
 */
export default function KeyStats({ items }) {
  return (
    <section className="-mt-px bg-dark pb-f156 pt-f112 tablet:pb-f78 tablet:pt-f55 mobile:pb-f48 mobile:pt-f30">
      <div className="relative px-gap">
        <div className="relative grid grid-cols-3 gap-f42 tablet:grid-cols-1 tablet:gap-f30 tablet:px-f71 mobile:gap-f52 mobile:px-0">
          {items.map((item) => (
            <div key={item.number} className="w-full">
              <KeyCard {...item} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
