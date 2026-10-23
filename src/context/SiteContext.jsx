import { createContext, useContext } from 'react'

/**
 * Shared chrome state provided by <Layout>.
 *  - lenis          Lenis instance (null until mounted)
 *  - isVisible      true once the preloader has finished (spec §2.1)
 *  - contactOpen    Contact overlay state (spec §2.6)
 *  - setContactOpen (bool | updater) => void
 */
export const SiteContext = createContext({
  lenis: null,
  isVisible: false,
  contactOpen: false,
  setContactOpen: () => {},
})

export const useSite = () => useContext(SiteContext)
