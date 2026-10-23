import Reveal from '../ui/Reveal.jsx'
import SectionTitle from '../ui/SectionTitle.jsx'
import SplitText from '../ui/SplitText.jsx'

/**
 * "Save the date" TextSection, descriptionSize "big" (spec §3.2).
 * Props: data — { number, title, subtitle, description }
 */
export default function SaveTheDate({ data }) {
  return (
    <section
      className="-mt-px bg-dark px-gap pb-f118 pt-f120 text-primary tablet:pb-f76 tablet:pt-f80 mobile:pb-f45 mobile:pt-f53"
      data-anim-group="save-the-date"
      data-anim-threshold="0.3"
    >
      <div className="relative">
        <SectionTitle number={data.number} title={data.title} className="mb-f82 tablet:mb-f70 mobile:mb-f34" />
        <div className="flex items-end justify-between tablet:flex-col tablet:items-start tablet:justify-start">
          <div className="w-f1470 shrink-0 tablet:w-f557 mobile:w-[87%]">
            <Reveal className="mb-f29 text-fmin16 uppercase leading-fmin-22-24 text-dark-grey tablet:mb-f12 mobile:mb-f10 mobile:text-fmin12">
              {data.subtitle}
            </Reveal>
            <SplitText
              as="p"
              text={data.description}
              stagger={0.02}
              duration={800}
              className="text-f95 font-light leading-f100 tablet:text-f36 tablet:leading-f38 mobile:text-f24 mobile:leading-f25"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
