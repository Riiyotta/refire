import Marquee from '../ui/Marquee.jsx'

/**
 * "Visit Us — " ticker (spec §3.6).
 * Props: data — { text, repeat }
 */
export default function Ticker({ data }) {
  return (
    <section
      className="relative -mt-px bg-dark pb-f160 pt-f140 text-primary tablet:pb-f65 tablet:pt-f68 mobile:py-f40"
      data-anim-group="ticker"
    >
      <Marquee
        text={data.text}
        repeat={data.repeat}
        itemClassName="whitespace-nowrap pr-f40 text-f250 capitalize leading-[1.05] tracking-[-.04em] tablet:pr-f28 tablet:text-f100 mobile:pr-f15 mobile:text-f64"
      />
    </section>
  )
}
