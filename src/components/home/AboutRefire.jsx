import Reveal from '../ui/Reveal.jsx'
import SplitText from '../ui/SplitText.jsx'

/**
 * "(About Refire)" TitleDescriptionSection, size "md" (spec §3.3).
 * Props: data — { title, description }
 */
export default function AboutRefire({ data }) {
  return (
    <section
      className="-mt-px bg-dark pb-f112 pt-f118 text-primary tablet:pb-f55 tablet:pt-f76 mobile:pb-f30 mobile:pt-f45"
      data-anim-group="about-refire"
      data-anim-threshold="0.3"
    >
      <div className="flex justify-between px-gap mobile:flex-col">
        <SplitText
          as="h2"
          text={data.title}
          stagger={0.03}
          className="text-f60 uppercase leading-[1.05] text-alt-dark-grey tablet:text-f36 mobile:mb-f29 mobile:text-f24"
        />
        <Reveal className="w-f722 text-f24 leading-[1.375] tablet:w-f342 tablet:text-fmin14 mobile:w-f294 mobile:text-fmin12 mobile:leading-[1.4]">
          {data.description}
        </Reveal>
      </div>
    </section>
  )
}
