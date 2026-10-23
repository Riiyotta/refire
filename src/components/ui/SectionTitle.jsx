import Line from './Line.jsx'
import Reveal from './Reveal.jsx'

/**
 * Section header row: line, then "NN" left / title right (spec §3.2 SectionTitle).
 *
 * Props:
 *  - number     left label, e.g. '01'
 *  - title      right label, e.g. 'Save the date'
 *  - isClear    true → no own side padding (default true, as on the home page)
 *  - className  extra classes on the root (e.g. margin-bottom)
 */
export default function SectionTitle({ number, title, isClear = true, className = '' }) {
  return (
    <div
      className={`relative text-fmin16 leading-fmin-22-24 uppercase tablet:text-fmin14 mobile:text-fmin12 ${
        isClear ? '' : 'px-gap'
      } ${className}`}
    >
      <Line delay={100} />
      <Reveal
        delay={200}
        className="flex justify-between pt-f22 tablet:pt-f30 mobile:pt-f15"
      >
        <span>{number}</span>
        <span>{title}</span>
      </Reveal>
    </div>
  )
}
