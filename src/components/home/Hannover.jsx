import Accordion from '../ui/Accordion.jsx'
import UnderlineLink from '../ui/UnderlineLink.jsx'

/**
 * Hannover Messe: title + content + accordion + contacts (spec §3.7).
 * Props: data — { title, contentTitle, contentSubtitle, contentText,
 *                 accordion: [{title, body}], contacts: [{label, email}] }
 */
export default function Hannover({ data }) {
  return (
    <section className="-mt-px bg-dark pb-f205 pt-f160 text-primary tablet:pb-f75 tablet:pt-f65 mobile:pb-f46 mobile:pt-f40">
      <div className="flex justify-between pl-gap pr-f204 tablet:px-gap mobile:flex-col mobile:justify-start">
        <h2 className="w-f352 flex-none text-f60 leading-f65 text-alt-dark-grey tablet:w-f197 tablet:text-f36 tablet:leading-f37 mobile:mb-f30 mobile:w-full mobile:text-f24 mobile:leading-f26">
          {data.title}
        </h2>
        <div className="w-f930 tablet:w-f487 mobile:w-full">
          <div className="relative">
            <div className="max-w-f726 tablet:max-w-f343 mobile:max-w-full">
              <div className="mb-f72 max-w-f600 tablet:mb-f53 tablet:max-w-f300 mobile:mb-f27 mobile:max-w-f260">
                <h3 className="mb-f14 text-f60 leading-f65 tablet:mb-f10 tablet:text-f28 tablet:leading-f36 mobile:text-f24 mobile:leading-f26">
                  {data.contentTitle}
                </h3>
                <p className="text-f18 leading-f33 text-alt-dark-grey tablet:max-w-f172 tablet:text-fmin12 tablet:leading-fmin-16-16 mobile:leading-[1.4]">
                  {data.contentSubtitle}
                </p>
              </div>
              <p className="text-f24 leading-f33 tablet:text-fmin14 tablet:leading-fmin-14-17 mobile:max-w-f294 mobile:text-fmin12 mobile:leading-[1.4]">
                {data.contentText}
              </p>
            </div>
            <Accordion items={data.accordion} className="mt-f119 tablet:mt-f63 mobile:mt-f54" />
            <div className="mt-f126 flex tablet:mt-f63 tablet:flex-col mobile:mt-f55">
              {data.contacts.map((c, i) => (
                <div
                  key={c.email}
                  className={`text-fmin16 leading-none mobile:text-fmin12 ${
                    i < data.contacts.length - 1 ? 'mr-f132 tablet:mb-f18 tablet:mr-0 mobile:mb-f14' : ''
                  }`}
                >
                  <span>{c.label}</span>
                  <UnderlineLink href={`mailto:${c.email}`}>{c.email}</UnderlineLink>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
