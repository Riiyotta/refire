import Layout from '../components/layout/Layout.jsx'
import Hero from '../components/home/Hero.jsx'
import SaveTheDate from '../components/home/SaveTheDate.jsx'
import AboutRefire from '../components/home/AboutRefire.jsx'
import KeyStats from '../components/home/KeyStats.jsx'
import ScrolledPicture from '../components/home/ScrolledPicture.jsx'
import Ticker from '../components/home/Ticker.jsx'
import Hannover from '../components/home/Hannover.jsx'
import TextImage from '../components/home/TextImage.jsx'
import * as home from '../data/home.js'

// Sections in spec DOM order (CLONE_SPEC.md §3); the footer (§3.9) is rendered by Layout.
export default function Home() {
  return (
    <Layout>
      <Hero data={home.hero} />
      <SaveTheDate data={home.saveTheDate} />
      <AboutRefire data={home.aboutRefire} />
      <KeyStats items={home.keyStats} />
      <ScrolledPicture data={home.scrolledPicture} />
      <Ticker data={home.ticker} />
      <Hannover data={home.hannover} />
      <TextImage data={home.textImage} />
    </Layout>
  )
}
