import { useEffect, useRef, useState } from 'react'
import gsap from '../../motion/gsap.js'
import { useSite } from '../../context/SiteContext.jsx'
import { contact as copy } from '../../data/site.js'
import { ArrowRightLong, ChevronDown } from '../ui/icons.jsx'
import BlackButton from '../ui/BlackButton.jsx'

const fieldText = 'text-f28 leading-[1.18] tablet:text-fmin16 tablet:leading-[1.45]'
const fieldLine = 'border-b-2 border-primary pb-f19 mobile:border-b'

/** Text input with overlay placeholder (opacity 1 → .5 while focused, spec §2.6). */
function Field({ name, placeholder, textarea = false }) {
  const [value, setValue] = useState('')
  const [active, setActive] = useState(false)
  const Control = textarea ? 'textarea' : 'input'
  return (
    <label className={`relative block ${fieldText}`}>
      <Control
        type={textarea ? undefined : 'text'}
        name={name}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onFocus={() => setActive(true)}
        onBlur={() => setActive(false)}
        className={`w-full resize-none bg-transparent outline-none ${fieldLine} ${
          textarea ? 'inline-block h-f315 align-baseline tablet:h-f163' : 'block'
        }`}
      />
      <span
        className={`pointer-events-none absolute left-0 top-0 select-none transition-opacity duration-100 ease-linear ${
          value ? 'opacity-0' : active ? 'opacity-50' : 'opacity-100'
        }`}
      >
        {placeholder}
      </span>
    </label>
  )
}

/** Department select (spec §2.6, row 1). */
function Select({ placeholder, options }) {
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState(null)
  const dropRef = useRef(null)
  const mounted = useRef(false)
  // Source: <Fade isVisible={open} duration={300}> → opacity fromTo, circ.inOut
  // both ways, pointer-events none while hidden.
  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      gsap.set(dropRef.current, { opacity: 0 })
      return
    }
    gsap.fromTo(
      dropRef.current,
      { opacity: open ? 0 : 1 },
      { opacity: open ? 1 : 0, duration: 0.3, ease: 'circ.inOut', overwrite: true },
    )
  }, [open])
  return (
    <div className={`relative ${fieldText}`}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`block w-full select-none pr-f24 text-left ${fieldLine}`}
        aria-expanded={open}
      >
        <span className="block w-full overflow-hidden text-ellipsis whitespace-nowrap">{value ?? placeholder}</span>
      </button>
      <ChevronDown
        className={`pointer-events-none absolute right-0 top-f12 h-f10 w-f16 fill-transparent transition-transform duration-300 ease-[ease] tablet:top-f7 mobile:top-f8 mobile:h-f12 mobile:w-f12 ${
          open ? 'rotate-180' : ''
        }`}
      />
      {/* Always mounted (source Select_dropdown): pointer-events none when closed;
          opacity is tweened by the effect above. */}
      <div
        ref={dropRef}
        className={`absolute left-0 top-f52 z-3 w-full border-2 border-gb bg-dark tablet:top-f40 ${
          open ? 'pointer-events-auto' : 'pointer-events-none'
        }`}
        data-anim="select-dropdown"
        aria-hidden={!open}
      >
          {options.map((opt) => (
            <button
              type="button"
              key={opt}
              tabIndex={open ? 0 : -1}
              onClick={() => {
                setValue(opt)
                setOpen(false)
              }}
              className={`select-option relative block w-full px-f25 py-f20 text-left tablet:px-f20 tablet:py-f16 ${
                value === opt ? 'is-selected' : ''
              }`}
            >
              <span className="relative inline-block">{opt}</span>
            </button>
          ))}
      </div>
    </div>
  )
}

/**
 * Contact overlay (spec §2.6), opened by the header pill.
 * Props: none — open state comes from SiteContext.
 */
export default function ContactOverlay() {
  const { contactOpen } = useSite()
  return (
    <div
      className={`contact-popup fixed left-0 top-0 z-89 h-auto max-h-screen w-full overflow-y-auto overscroll-contain bg-dark [scrollbar-width:none] [&::-webkit-scrollbar]:hidden ${contactOpen ? 'is-open' : ''}`}
      aria-hidden={!contactOpen}
      // The source scrolls the popup with its own virtual scroll while the page
      // behind stays put; here the overlay scrolls natively (Lenis ignores it)
      // and Layout stops Lenis while it is open.
      data-lenis-prevent
    >
      <div className="flex min-h-screen flex-col">
        <div className="mt-auto">
          <div className="relative flex justify-between bg-dark px-gap pb-f54 pt-f100 text-fmin16 leading-fmin-22-24 text-primary tablet:text-fmin14 tablet:leading-fmin-18-20 mobile:flex-col mobile:pb-f10 mobile:pt-f124">
            {/* Left */}
            <div className="w-f800 flex-none tablet:w-f340 mobile:w-full">
              <a
                href={copy.titleHref}
                target="_blank"
                rel="noreferrer"
                className="mb-f104 block text-f176 capitalize leading-[1.02] tracking-[-.01em] transition-opacity duration-300 ease-[ease] hov:opacity-60 tablet:mb-f44 tablet:text-f80 mobile:mb-f30 mobile:text-f40"
              >
                <span className="flex items-center">
                  {copy.titleLines[0]}
                  <ArrowRightLong className="ml-f48 h-f76 w-f89 flex-none tablet:ml-f20 tablet:h-f30 tablet:w-f36 mobile:ml-f15 mobile:h-f16 mobile:w-f19" />
                </span>
                <span className="inline-block overflow-hidden align-baseline">{copy.titleLines[1]}</span>
              </a>
              <div className="max-w-f373 tablet:max-w-f268">
                <div className="uppercase text-dark-grey tablet:text-fmin16 tablet:leading-fmin-22-24 mobile:text-fmin14">
                  {copy.formTitle}
                </div>
                <p className="mt-f10 tablet:mt-f3 mobile:mt-f5">{copy.formText}</p>
              </div>
              <div className="mt-f84 flex tablet:mt-f40 tablet:flex-col mobile:mt-f30">
                {copy.lists.map((list, i) => (
                  <div
                    key={list.title}
                    className={`max-w-f373 tablet:max-w-f268 ${i < copy.lists.length - 1 ? 'mr-f85 tablet:mr-0' : ''} ${
                      i > 0 ? 'tablet:mt-f40 mobile:mt-f30' : ''
                    }`}
                  >
                    <div className="uppercase text-dark-grey tablet:text-fmin16 tablet:leading-fmin-22-24 mobile:text-fmin14">
                      {list.title}
                    </div>
                    <div className="mt-f10 tablet:mt-f3 mobile:mt-f5">
                      {list.lines.map((line) =>
                        typeof line === 'string' ? (
                          <p key={line}>{line}</p>
                        ) : (
                          <p key={line.href}>
                            {line.prefix} <a href={line.href}>{line.text}</a>
                          </p>
                        ),
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: form */}
            <div className="w-f783 flex-none pt-f30 tablet:w-f270 tablet:pt-0 mobile:mt-f70 mobile:w-full">
              <form className="relative" onSubmit={(e) => e.preventDefault()} noValidate>
                <div className="grid grid-cols-[100%] gap-y-f52 tablet:gap-y-f48">
                  <Select placeholder={copy.select.placeholder} options={copy.select.options} />
                  {copy.rows.map((row, i) => (
                    <div key={i} className="grid grid-cols-2 gap-x-f40 tablet:gap-x-f20 mobile:gap-x-f27">
                      {row.map((f) => (
                        <Field key={f.name} name={f.name} placeholder={f.placeholder} />
                      ))}
                    </div>
                  ))}
                  <Field name={copy.message.name} placeholder={copy.message.placeholder} textarea />
                </div>
                <div className="mt-f30 flex items-end justify-between tablet:flex-col-reverse tablet:items-center">
                  <p className="w-f382 text-f16 leading-f24 text-dark-grey tablet:mt-f40 tablet:max-w-full tablet:text-fmin12 tablet:leading-[1.4]">
                    {copy.note}
                  </p>
                  <div className="text-center mobile:w-f175">
                    <BlackButton type="submit" className="mobile:w-full">{copy.submit}</BlackButton>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
