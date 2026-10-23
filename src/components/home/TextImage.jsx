import LinkArrow from '../ui/LinkArrow.jsx'
import Reveal from '../ui/Reveal.jsx'
import ShaderPicture from '../ui/ShaderPicture.jsx'
import SplitText from '../ui/SplitText.jsx'

/**
 * Text + WebGL image, isReverse (spec §3.8): image left, text right.
 * Props: data — { title, text, links: [{label, href}], image }
 */
export default function TextImage({ data }) {
  return (
    <section className="-mt-px bg-dark pb-f115 pt-f205 text-primary tablet:py-f75 mobile:pb-f70 mobile:pt-f46">
      <div className="relative flex h-f1143 flex-row-reverse justify-between px-gap tablet:h-f500 mobile:h-auto mobile:flex-col-reverse">
        {/* Text item */}
        <div className="relative flex w-full max-w-half-f15 flex-col items-center mobile:max-w-none mobile:items-start">
          <div
            className="my-auto mr-f80 max-w-f630 self-end tablet:mr-0 tablet:max-w-f290 mobile:self-auto"
            data-anim-group="text-image"
            data-anim-threshold="0.3"
          >
            <SplitText
              as="h2"
              text={data.title}
              stagger={0.1}
              duration={800}
              className="mb-f72 text-f60 capitalize leading-[1.05] tablet:mb-f46 tablet:text-f32 mobile:mb-f14 mobile:max-w-[88%] mobile:text-f24 mobile:leading-[1.11]"
            />
            <Reveal
              delay={500}
              className="max-w-f413 text-f24 leading-[1.375] tablet:max-w-f293 tablet:text-fmin12 tablet:leading-[1.4]"
            >
              {data.text}
            </Reveal>
            <Reveal delay={500} className="mt-f80 flex flex-col items-start tablet:mt-f42 mobile:mt-f29">
              {data.links.map((l) => (
                <LinkArrow key={l.href + l.label} href={l.href} target="_blank" rel="noopener noreferrer">
                  {l.label}
                </LinkArrow>
              ))}
            </Reveal>
          </div>
        </div>
        {/* Image item */}
        <div className="relative flex w-full max-w-half-f15 flex-col items-center tablet:max-w-half-f10 mobile:mb-f57 mobile:h-f418 mobile:max-w-none mobile:items-start">
          <div className="absolute left-0 top-0 h-full w-full">
            <ShaderPicture src={data.image} />
          </div>
        </div>
      </div>
    </section>
  )
}
