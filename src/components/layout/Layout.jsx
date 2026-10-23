import { useEffect, useMemo, useState } from 'react'
import gsap from '../../motion/gsap.js'
import { useReveals } from '../../motion/reveal.js'
import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import { SiteContext } from '../../context/SiteContext.jsx'
import Preloader from './Preloader.jsx'
import Header from './Header.jsx'
import ScrollProgress from './ScrollProgress.jsx'
import Cursor from './Cursor.jsx'
import CookiePane from './CookiePane.jsx'
import ContactOverlay from './ContactOverlay.jsx'
import Footer from './Footer.jsx'

/**
 * Wraps a route's content with the site chrome (spec §2) and Lenis smooth
 * scroll (spec §0.1 recommendation: lerp 0.1, wheelMultiplier 1, smoothWheel).
 * Lenis is driven from the GSAP ticker so Animation can share one clock.
 *
 * Props:
 *  - children       page sections
 *  - className      classes on the page root (default: Home_root colours,
 *                   bg primary / text dark, spec §3)
 *  - showFooter     render the Copyright footer (default true)
 *  - preloader      render the preloader on mount (default true)
 *  - showProgress   render the fixed page-progress bar (default true; the
 *                   source mounts it from the Home page only, not on _error)
 */
export default function Layout({
  children,
  className = 'relative bg-primary text-dark',
  showFooter = true,
  preloader = true,
  showProgress = true,
}) {
  const [lenis, setLenis] = useState(null)
  const [isVisible, setVisible] = useState(!preloader)
  const [contactOpen, setContactOpen] = useState(false)

  useEffect(() => {
    const instance = new Lenis({ lerp: 0.1, wheelMultiplier: 1, smoothWheel: true })
    const tick = (time) => instance.raf(time * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    setLenis(instance)
    return () => {
      gsap.ticker.remove(tick)
      instance.destroy()
    }
  }, [])

  // Entrance / scroll-reveal motion for every [data-anim-group] (src/motion/reveal.js)
  useReveals(isVisible)

  // Body scroll lock while the Contact overlay is open (the source page does
  // not move under the popup).
  useEffect(() => {
    if (!lenis) return
    if (contactOpen) lenis.stop()
    else lenis.start()
  }, [lenis, contactOpen])

  const value = useMemo(
    () => ({ lenis, isVisible, contactOpen, setContactOpen }),
    [lenis, isVisible, contactOpen],
  )

  return (
    <SiteContext.Provider value={value}>
      {!isVisible && <Preloader onComplete={() => setVisible(true)} />}
      <Header />
      {showProgress && <ScrollProgress />}
      <ContactOverlay />
      <CookiePane />
      <Cursor />
      <main className={className}>
        {children}
        {showFooter && <Footer />}
      </main>
    </SiteContext.Provider>
  )
}
