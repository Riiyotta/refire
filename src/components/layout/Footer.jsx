import { useSite } from '../../context/SiteContext.jsx'
import { footer as copy } from '../../data/site.js'
import { ArrowUp } from '../ui/icons.jsx'

/**
 * Footer copyright row (spec §3.9). Back to Top scrolls to 0 through Lenis
 * (lerp-based smooth scroll).
 * Props: className (extra classes on the section).
 */
export default function Footer({ className = '' }) {
  const { lenis } = useSite()
  const year = new Date().getFullYear()
  return (
    <footer
      className={`-mt-px bg-dark px-gap pt-f115 text-primary tablet:pt-f75 mobile:pt-f70 ${className}`}
    >
      <div className="grid grid-cols-3 border-t border-darkness-grey pb-f25 pt-f42 text-f20 leading-[1.2] tablet:pb-f14 tablet:pt-f24 tablet:text-fmin16 mobile:pb-f10 mobile:pt-f20 mobile:text-fmin12">
        <div className="uppercase">{`${copy.brand} ©${year}`}</div>
        <div className="text-center capitalize">{copy.rights}</div>
        <div className="text-right capitalize">
          <button
            type="button"
            className="inline-flex items-center capitalize"
            onClick={() => (lenis ? lenis.scrollTo(0) : window.scrollTo(0, 0))}
          >
            {copy.backToTop}
            <ArrowUp className="ml-f10 h-f12 w-f14 flex-none tablet:h-f8 tablet:w-f10" />
          </button>
        </div>
      </div>
    </footer>
  )
}
